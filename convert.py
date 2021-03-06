#! sfyt-env\Scripts\python.exe
import datetime
from getpass import getpass
from inspect import _void
import os
import sys
import re
import time
import logging

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC, select
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from yt_api import *
from selenium_helper import *
from sqlite_handler import *

from configparser import ConfigParser
import chromedriver_autoinstaller


class Yt_sptfy_converter:


    def __init__(self):
        
        # Load Api do quota check
        self.yt_api = Yt_api()
        _ = self.yt_api.get_user_channel()['items'][0]["id"]

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename='scripttest.log', encoding='utf-8', level=logging.INFO)



        self.sql = Sqlite_handler("progress.sqlite")

        self.debugmode = True


        def initialize_chromedriver() -> webdriver.Chrome:
            chromedriver_autoinstaller.install()
            options = Options()
            # options.add_argument("--start-maximized")
            options.add_argument('ignore-certificate-errors')
            options.add_argument("--enable-webgl")
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            if not self.debugmode: 
                options.add_argument('log-level=2')
                options.add_argument("--headless") 
            driver = webdriver.Chrome(options=options)


            # Check if driver version matches chrome installation
            str1 = driver.capabilities['browserVersion']
            str2 = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
            if str1[0:2] != str2[0:2]:  
                logging.error("chromedriver_autoinstaller, failed to install matching chromedriver version. \nDownload manually from https://chromedriver.chromium.org/downloads and add path to driver initialisation")
                sys.exit(2)
            return driver

        self.driver = initialize_chromedriver()
        

        # # Connect to spotify account
        # # Get Spotify Credentials
        # self.loginName = config["spotify"]["accountNameOrEmail"]
        # if config["spotify"]["password"] != None:
        #     self.pw = config["spotify"]["password"]
        # else:
        #     self.pw = getpass('Password: ')
        # self.open_spotify_session()

        # def sync_user_profile(profile_link) -> list[str]:
        #     return [link for link in self.get_playlistlinks_from_profile(profile_link)]

        self.convert_links_in_config()
        
    
    def convert_links_in_config(self, configname: str = "config.ini"):

        # Read Configfile
        configfile = configname
        config = ConfigParser()
        config.read(configfile)

        # add all links in config to db if not present
        links = list(map(self.import_link, [config["sync_links"][entry] for entry in config["sync_links"]]))
        concat_links = [jj for subl in links for jj in subl]
        # update playlistnames in db
        list(map(self.update_playlist_info, concat_links))
        for link in concat_links:
            id = self.update_playlist(link)
            self.sync_tracks_yt(id)


    def update_playlist(self, spotify_link: str) -> int:
        
        pk, p_name = self.sql.q_exec('SELECT id, name FROM Playlists WHERE sp_link=?', (spotify_link,)).fetchone()
        # create youtube playlist if not present
        if not (yt_id := self.sql.q_exec('SELECT yt_id FROM Playlists WHERE ID=?', (pk,)).fetchone()[0]):
            p_name:str = p_name.replace("&", "and")
            yt_id = self.yt_api.create_playlist(p_name)["id"]
            self.sql.q_exec('UPDATE Playlists SET yt_id=? WHERE sp_link=?', (yt_id, spotify_link))
        # create table in database if not present
        t_name = f'Playlist_{pk}'
        self.sql.create_table_from_preset('Playlist_template', t_name)
        # get entrys in db
        db_entrys = self.sql.q_exec(f'SELECT ID, track, artists FROM {t_name}').fetchall()
        # get entrys in spotify
        tracks_artists = self.get_tracks_and_artists(spotify_link)
        # list for items to be removed from db and yt_playlist
        self.remove_tracks(t_name, tuple(id for id, tr, at in db_entrys if (tr, at) not in tracks_artists))
        # list of items to be added to db and spotify
        new_too_add = [(tr, at) for tr, at in tracks_artists if not self.sql.get_entry_count(f'track=? AND artists=?', t_name, (tr, at))]
        # add new tracks to db
        self.sql.q_exec_many(f'INSERT INTO {t_name} (track, artists) VALUES (?, ?)', new_too_add)
        return pk


    def import_link(self, spotify_link: str) -> list[str]:

        def get_playlist_links(raw_link) -> list[str]:
            # Remove quotation if given in config
            re_subs = [(r"^'''", ""), (r"^\"", ""), (r"^'", ""), (r"'''$", ""), (r"\"$", ""), (r"'$", ""), (r"\?.*=.*", "")]
            raw_link = self.re_sub_list(raw_link, re_subs)
            if re.search(r"^https://open.spotify.com/playlist/", raw_link):
                return [raw_link]
            if re.search(r"^https://open.spotify.com/user/", raw_link):
                return self.get_playlistlinks_from_profile(raw_link)
                # return [get_playlist_links(link) for link in sync_user_profile(raw_link)]
            logging.info(f'{raw_link} did not match user or playlist regex')

        # parse links
        linklist = get_playlist_links(spotify_link)
        # add to playlists to db if not present
        links_in_db = [link[0] for link in self.sql.q_exec('SELECT sp_link FROM Playlists').fetchall()]
        links_to_add = [(link,) for link in linklist if not link in links_in_db]
        self.sql.q_exec_many("INSERT INTO Playlists (sp_link) VALUES (?)", links_to_add)
        return linklist


    def sync_tracks_yt(self, pk: int):
        add = self.sql.q_exec(f'SELECT track, artists FROM Playlist_{pk} WHERE yt_id IS NULL').fetchall()
        playlist_id: str = self.sql.q_exec(f'SELECT yt_id FROM Playlists WHERE ID = ?', (pk,)).fetchone()[0]
        for tr, at in add:
            vid_id = self.get_yt_id_from_keywords([tr, at])
            if not vid_id: continue
            yt_id = self.yt_api.add_item_to_playlist(playlist_id, vid_id)["id"]
            self.sql.q_exec(f"UPDATE Playlist_{pk} SET yt_id = ? WHERE track = ? AND artists = ?", (yt_id, tr, at))


    def remove_tracks(self, tablename: str, keys: tuple):
        if len(keys) == 1:
            remove = self.sql.q_exec(f'SELECT ID, yt_id FROM {tablename} WHERE ID = ?', (keys[0],)).fetchall()
        else:
            remove = self.sql.q_exec(f'SELECT ID, yt_id FROM {tablename} WHERE ID IN {keys}').fetchall()
        self.sql.q_exec_many(f"DELETE FROM {tablename} WHERE ID = ?", [(id,) for id, _ in remove])
        list(map(self.yt_api.delete_item_from_playlist, [yt_id for _, yt_id in remove if yt_id]))


    def update_playlist_info(self, spotify_link:str):  
        name = self.get_playlist_name(spotify_link)
        self.sql.q_exec(f"UPDATE Playlists SET name = ? WHERE sp_link = ?", (name, spotify_link))
        creator = self.get_playlist_creator(spotify_link)
        self.sql.q_exec(f"UPDATE Playlists SET creator = ? WHERE sp_link = ?", (creator, spotify_link))


    @staticmethod
    def re_sub_list(string_to_edit: str, regex_list: list[(str, str), ]) -> str:
        """funktion that will repeatedly will call re.sub and return endresult

        Args:
            string_to_edit (str): raw string
            regex_list (list[(str, str),]): list of tuples (regex, replacement)

        Returns:
            str: edited string
        """
        for tup in regex_list:
            string_to_edit = re.sub(tup[0], tup[1], string_to_edit)
        return string_to_edit


    def get_tracks_and_artists(self, spotify_link: str) -> list[(str, str), ]:
        """
        Args:
            spotify_link (str): spotify webplayer link to playlist

        Returns:
            list[(str, str),]: list of tuples containing (title, artits) of tracks in playlist
        """
        
        tracklist: list[(str, str),] = []
            
        self.driver.get(spotify_link)
        parentElement = wait_for_element(By.XPATH, '''//*[@id="main"]/div/div[2]/div[3]/main/div[2]/div[2]/div/div/div[2]/section/div[2]/div[3]/div[1]''', self.driver)
        if not parentElement:
            return self.get_tracks_and_artists(spotify_link)

        subElementList: list[WebElement] = []
        while True:
            # Wait for page to load
            time.sleep(0.5)
            found_elements = parentElement.find_elements(By.CSS_SELECTOR, '''div[role='row']''')
            new_elements = [elem for elem in found_elements if not elem in subElementList]
            subElementList.extend(new_elements)

            # extract relevant info from new Webelements
            for element in new_elements:
                lines: list[str] = element.text.splitlines()
                # the structure of lines:
                # ['title', (optional 'E' tag), 'artist', 'album', 'time_since_added_to_playlist', 'duration']
                if lines[2] == 'E':
                    tracklist.append((lines[1], lines[3]))
                else:
                    tracklist.append((lines[1], lines[2]))

            # if new elements are found scroll to last element 
            if not new_elements: break
            actions = ActionChains(self.driver)
            actions.move_to_element(new_elements[-1])
            actions.perform()

        del tracklist[0]
        return tracklist
        

    def open_spotify_session(self):

        # Open Link
        self.driver.get(r"https://www.spotify.com")

        # Navigate to loginpage
        confirmkey = wait_for_element(By.XPATH, '''//*[@id="__next"]/div[1]/header/div/nav/ul/li[6]/a''', self.driver)
        confirmkey.click()

        # Confirm login
        loginformUsername = wait_for_element(By.NAME, '''username''', self.driver)
        loginformUsername.send_keys(self.loginName)

        self.driver.find_element_by_name('''password''').send_keys(self.pw)
        self.driver.find_element_by_id("login-button").click()

        if (confirmButton := wait_for_element(By.ID, '''onetrust-accept-btn-handler''', self.driver)):
            confirmButton.click()


    def get_yt_link_from_query(self, query: str) -> str:
        '''query example: "searchterm1+searchterm2"'''
        self.driver.get("https://www.youtube.com/results?search_query="+query)

        if (confirmkey := wait_for_element(By.XPATH, '''//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[4]/form/div[1]/div/button/span''', self.driver, timeout=3)):
            confirmkey.click()
        
        if not (resultlist := wait_for_element(By.XPATH, '''//*[@id="page-manager"]/ytd-search''', self.driver, timeout=30)):
            return False

        # search for valid link
        for link in resultlist.find_elements(By.TAG_NAME, 'a'):
            href = str(link.get_attribute('href'))
            if not href is None and re.search(r"^https://www.youtube.com/watch", href) and not re.match(r"\&list=", href):
                # add filter for r"[Clean]", r"[clean]"
                return(href)
        self.logger.error(f"no video found for {query=}")
        return ""

        
    def get_yt_id_from_keywords(self, keywords:list) -> str | None:

        raw_query = ' '.join(keywords)
        re_subs = [(r"\&+", r"+"), (r"\s+", r"+"), (r",+", r"+"), (r"-+", r"+"), (r"\++", r"+")]
        new_query = self.re_sub_list(raw_query, re_subs)
        if (yt_id := re.search(r"/?v=(.*)", self.get_yt_link_from_query(new_query))):
            return yt_id[1]
        return None


    def get_playlist_name(self, spotify_link) -> str:
        try:
            self.driver.get(spotify_link)
            return wait_for_element(By.CLASS_NAME, '''Afp2Urf1F4Ub6nHGSF9i''', self.driver).text
        except Exception as err:
            self.logger.error(err)
            self.logger.error("could not find playlist name, classname of element might be deprecated!")
            return "<[NAME NOT FOUND]>"

    
    def get_playlist_creator(self, spotify_link) -> str:
        try:
            self.driver.get(spotify_link)
            return wait_for_element(By.CLASS_NAME, '''Czg_RoYmXG0FPTHG9Kdb''', self.driver).text
            # self.driver.get(spotify_link)
            # parentelem = wait_for_element(By.CLASS_NAME, '''FCLMqGL8hF5PIoL6VSbc''', self.driver)
            # return parentelem.text.splitlines()[0]
        except Exception as err:
            self.logger.error(err)
            self.logger.error("could not find playlist creator, classname of element might be deprecated!")
            return "<[CREATOR NOT FOUND]>"


    def get_playlistlinks_from_profile(self, profile_link) -> list[str]:

        link_to_playlists = profile_link + "/playlists"
        self.driver.get(link_to_playlists)
        playlists_field = wait_for_element(By.XPATH, '''//*[@id="main"]/div/div[2]/div[3]/main/div[2]/div[2]/div/div/div[2]/section/section/div[2]''', self.driver)
        list_link_objects = playlists_field.find_elements(By.TAG_NAME, 'a')
        return [item.get_attribute('href') for item in list_link_objects]
        

               


def main():

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    Yt_sptfy_converter().convert_links_in_config()

if __name__ == "__main__":
    main()