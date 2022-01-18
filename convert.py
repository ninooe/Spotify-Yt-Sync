
#! sfyt-env\Scripts\python.exe
import datetime
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
from read_yaml import read_yml_file


import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from yt_api import *
from selenium_helper import *

import sqlite_handler

from configparser import ConfigParser
import chromedriver_autoinstaller


class Yt_sptfy_converter:


    def __init__(self):


        # Read Configfile
        self.configname = "config.ini"
        configfile = self.configname
        self.config = ConfigParser()
        self.config.read(configfile)

        for key, var in self.config["spotify"].items():
            os.environ[key] = var

        # load apilib
        self.yt_api = Yt_api()
        # quota check
        _ = self.yt_api.get_user_channel()['items'][0]["id"]

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename='scripttest.log', encoding='utf-8', level=logging.INFO)

        # load spotify apilib
        self.spty_api = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

        # get sql handler
        self.sql = sqlite_handler.Sqlite_handler("progress.sqlite")

        self.debugmode = True

        self.test()


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
        

        self.convert_links_in_config()
        
    def test(self):

        # print(self.spty_api.track(self.sql.q_exec("SELECT sp_ID FROM track WHERE ID = 1").fetchone()[0]))
        self.playlist_from_spotify("5mxDiK1jscv6V0EtYdRp0z")
        sys.exit()


    def link2id(link):
        link = re.search(r"\/([^/]+)$", link)[1]
        if (match := re.search(r"watch\?v=([a-zA-Z0-9]+)", link)):
            link = match[1]
        return re.search(r"^([a-zA-Z0-9]+)", link)[1]
  

    def add_artist(self, sp_ID: str, name: str = None) -> int:
        if (id := self.sql.q_exec("SELECT ID FROM artist WHERE sp_ID=?", (sp_ID,)).fetchone()):
            return id[0]
        if not name:
            name = self.spty_api.artist(sp_ID)["name"]
        return self.sql.q_exec('INSERT INTO artist (sp_ID, name) VALUES (?, ?)', (sp_ID, name)).lastrowid


    def add_track(self, sp_ID: str, name: str = None, artist_ids: list = None) -> int:
        if (id := self.sql.q_exec("SELECT ID FROM track WHERE sp_ID=?", (sp_ID,)).fetchone()):
            return id[0]
        if not name or not artist_ids:
            api_result = self.spty_api(sp_ID)
            name = api_result["name"]
            artist_ids = [aid["id"] for aid in api_result["artists"]]
        track_id = self.sql.q_exec('INSERT INTO track (sp_ID, name) VALUES (?, ?)', (sp_ID, name)).lastrowid
        [self.link_artist_to_track(aid, track_id) for aid in artist_ids]
        return track_id


    def add_playlist(self, sp_ID: str, name: str = None) -> int:
        if (resp := self.sql.q_exec("SELECT ID, name FROM playlist WHERE sp_ID=?", (sp_ID,)).fetchone()):
            return resp[0]
        if not name:
            name = self.spty_api.playlist(sp_ID)["name"]
        return self.sql.q_exec('INSERT INTO playlist (sp_ID, name) VALUES (?, ?)', (sp_ID, name)).lastrowid

        
    def link_artist_to_track(self, artist_id, track_id):
        if self.sql.q_exec("SELECT * FROM artist_track_mm WHERE track_id=? AND artist_id=?", (track_id, artist_id)).fetchone():
            return
        self.sql.q_exec("INSERT INTO artist_track_mm (track_ID, artist_ID) VALUES (?, ?)", (track_id, artist_id))
        
        
    def link_playlist_to_track(self, playlist_id, track_id):
        if self.sql.q_exec("SELECT * FROM playlist_track_mm WHERE track_id=? AND playlist_id=?", (track_id, playlist_id)).fetchone():
            return
        self.sql.q_exec("INSERT INTO playlist_track_mm (track_ID, playlist_ID) VALUES (?, ?)", (track_id, playlist_id))
        

    def playlist_from_spotify(self, sp_ID):
        # get information from spotify api
        playlist_items = []
        api_result = self.spty_api.playlist_items(sp_ID, additional_types=("track",))
        while api_result:
            for item in api_result["items"]:
                artists = [{"name": artist["name"], "sp_ID": artist["id"]} for artist in item["track"]["artists"]]
                # add artists to db if not present and get id
                artist_ids = [self.add_artist(**k) for k in artists]
                playlist_items.append({
                    "name": item["track"]["name"],
                    "sp_ID": item["track"]["id"],
                    "artist_ids": artist_ids
                })
            if api_result['next']:
                api_result = self.spty_api.next(api_result)
            else:
                api_result = None
        # add tracks to database
        track_ids = [self.add_track(**k) for k in playlist_items]
        playlist_id = self.add_playlist(sp_ID, )
        [self.link_playlist_to_track(playlist_id, tid) for tid in track_ids]




        
        
                

        # artists_uniqe = set([jj for subl in [item["artists"] for item in playlist_items] for jj in subl])

        # write to db
        # list(dict.fromkeys(
                # artist_ids = [self.add_artist(**k) for k in artists]

                # track_id = self.add_track(item["id"])
                # for artist in item["track"]["artists"]:
                #     artist_id = self.add_artist(artist["id"], artist["name"])
                #     self.link_artist_to_track(track_id, artist_id)

















    def convert_links_in_config(self):

        # add all links in config to db if not present
        links = list(map(self.import_link, [self.config["sync_links"][entry] for entry in self.config["sync_links"]]))
        concat_links = [jj for subl in links for jj in subl]


        # update playlistnames in db
        list(map(self.update_playlist_info, concat_links))
        for link in concat_links:
            id = self.update_playlist(link)
            # self.sync_tracks_yt(id)

    def playlist_to_youtube(self, playlist_id: str) -> int:
        pk, p_name = self.sql.q_exec('SELECT ID, name FROM playlist WHERE sp_link=?', (spotify_id,)).fetchone()
        # create youtube playlist if not present
        yt_p_name: str = p_name.replace("&", "and")
        if not (yt_id := self.sql.q_exec('SELECT yt_id FROM playlist WHERE ID=?', (pk,)).fetchone()[0]):
            yt_id = self.yt_api.create_playlist(yt_p_name)["id"]
            self.sql.q_exec('UPDATE playlist SET yt_id=? WHERE sp_link=?', (yt_id, spotify_id))
        # update name in yt if changed
        if not self.yt_api.list_playlist(yt_id)["items"][0]["snippet"]["localized"]["title"] == yt_p_name:
            self.yt_api.update_playlist(yt_id, snippet={"title": yt_p_name})
        # get entrys in spotify
        tracks_artists = self.get_tracks_and_artists(spotify_id)
        return pk

        # get entrys in db
        db_entrys = self.sql.q_exec(f'SELECT ID, track, artists FROM {t_name}').fetchall()
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
        links_in_db = [link[0] for link in self.sql.q_exec('SELECT sp_link FROM playlist').fetchall()]
        links_to_add = [(link,) for link in linklist if not link in links_in_db]
        self.sql.q_exec_many("INSERT INTO playlist (sp_link) VALUES (?)", links_to_add)
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
        self.sql.q_exec(f"UPDATE playlist SET name = ? WHERE sp_link = ?", (name, spotify_link))

        # creator = self.get_playlist_creator(spotify_link)
        # self.sql.q_exec(f"UPDATE playlist SET creator = ? WHERE sp_link = ?", (creator, spotify_link))


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

        
    def get_yt_id_from_keywords(self, keywords: list) -> str | None: 

        raw_query = ' '.join(keywords)
        re_subs = [(r"\&+", r"+"), (r"\s+", r"+"), (r",+", r"+"), (r"-+", r"+"), (r"\++", r"+")]
        new_query = self.re_sub_list(raw_query, re_subs)
        if (yt_id := re.search(r"/?v=(.*)", self.get_yt_link_from_query(new_query))):
            return yt_id[1]
        return None


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

    Yt_sptfy_converter()

if __name__ == "__main__":
    main()