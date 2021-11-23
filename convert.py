import datetime
from getpass import getpass
import os
from os import name
import sys
import re
import time
import json
import logging

import yt_api as yt_api_obj
import sqlite_handler as sqlite

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from configparser import ConfigParser
import chromedriver_autoinstaller

print(type(By.CSS_SELECTOR))

def reg_is_in_filter(filters: list, body: str) -> bool:
    for filter in filters:
        if re.search(filter, body):
            return True
    return False

def sel_helper_wait_for_elem(locator: str, query: str, driver: selenium.webdriver, timeout: int = 30):
    """Let selenium driver wait for element

    Args:
        locator (str): locator present in this set selenium.webdriver.common.by
        query (str): description of element matching locator
        driver (webdriver): instance of selenium.webdriver
        timeout (int, optional): time to wait before timeout. Defaults to 30.

    Returns:
        selenium.webdriver.remote.webelement.WebElement / None
    """
    try:
        parentElement = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((locator, query))
            )
        return parentElement
    except Exception:
        logging.debug(f"{Exception} occured while waiting for element")
        return None
    

class Yt_sptfy_converter:


    def __init__(self):

        # # Load Api do quota check
        # self.yt_api = yt_api_obj.Yt_api()
        # _ = self.yt_api.get_user_channel()['items'][0]["id"]

        # Read Configfile
        configfile = "config.ini"
        config = ConfigParser()
        config.read(configfile)


        # Load progress tracker
        self.path_to_progress_json = "./progress.json"
        try:
            with open(self.path_to_progress_json) as f:
                self.progress_dict = json.load(f)
        except:
            self.progress_dict = {}



        def initialize_chromedriver() -> webdriver.Chrome:
            chromedriver_autoinstaller.install()
            options = Options()
            # options.add_argument("--start-maximized")
            options.add_argument('ignore-certificate-errors')
            options.add_argument("--enable-webgl")
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            driver = webdriver.Chrome(options=options)


            # Check if driver version matches chrome installation
            str1 = driver.capabilities['browserVersion']
            str2 = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
            if str1[0:2] != str2[0:2]:  
                logging.error("chromedriver_autoinstaller, failed to install matching chromedriver version. \nDownload manually from https://chromedriver.chromium.org/downloads and add path to driver initialisation")
                sys.exit(2)
            return driver

        self.driver = initialize_chromedriver()
        
        # # Get Spotify Credentials
        # self.loginName = config["spotify"]["accountNameOrEmail"]
        # if config["spotify"]["password"] != None:
        #     self.pw = config["spotify"]["password"]
        # else:
        #     self.pw = getpass('Password: ')
        

        # # Convert 
        # self.open_spotify_session()


        for entry in config["sync_links"]:
            link = config["sync_links"][entry]
            # Remove quotation if given in config
            re_subs = [(r"^'''", ""), (r"^\"", ""), (r"^'", ""), (r"'''$", ""), (r"\"$", ""), (r"'$", "")]
            link = self.re_sub_list(link, re_subs)
            if re.search(r"^https://open.spotify.com/user/", link):
                self.sync_user_profile(link)
            if re.search(r"^https://open.spotify.com/playlist/", link):
                self.convert_playlist(link)
            else: 
                logging.info(f'{link} did not match user or playlist regex')

    @staticmethod
    def re_sub_list(string_to_edit:str, regex_list:list[(str, str),]) -> str:
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

    def get_tracks_and_artists(self, spotify_link) -> list[(str, str), ]:
        
 
        self.driver.get(spotify_link)
        parentElement = sel_helper_wait_for_elem(By.XPATH, '''//*[@id="main"]/div/div[2]/div[3]/main/div[2]/div[2]/div/div/div[2]/section/div[2]/div[3]/div[1]''', self.driver)
        if not parentElement:
            return self.get_tracks_and_artists(spotify_link)

        subElementList: list[selenium.webdriver.remote.webelement.WebElement] = []
        while True:
            # Wait to load page
            time.sleep(0.5)
            found_elements = parentElement.find_elements_by_css_selector('''div[role='row']''')
            new_elements = [elem for elem in found_elements if not elem in subElementList]
            subElementList.extend(new_elements)
            # if new elements are found scroll to last element
            if not new_elements: break
            actions = ActionChains(self.driver)
            actions.move_to_element(new_elements[-1])
            actions.perform()
        # extract relevant info from found Webelements
        tracklist: list[(str, str),] = []
        for element in subElementList[1:]:
            lines: list[str] = element.text.splitlines()
            # lines:
            # ['title', (optional 'E' tag), 'artist', 'album', 'time_since_added_to_playlist', 'duration']
            if lines[1] == 'E':
                tracklist.append((lines[0], lines[2]))
            else:
                tracklist.append((lines[0], lines[1]))

        return tracklist


    def open_spotify_session(self):

        # Open Link
        self.driver.get(r"https://www.spotify.com")

        # Navigate to loginpage
        confirmkey = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '''//*[@id="__next"]/div[1]/header/div/nav/ul/li[6]/a'''))
        )
        confirmkey.click()

        # Confirm login
        loginformUsername = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.NAME, '''username'''))
        )
        loginformUsername.send_keys(self.loginName)

        self.driver.find_element_by_name('''password''').send_keys(self.pw)
        self.driver.find_element_by_id("login-button").click()

        try:
            confirmButton = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, '''onetrust-accept-btn-handler'''))
            )
            confirmButton.click()
        except:
            pass


    def get_link_to_video_by_query(self, query):
        '''query example: "searchterm1+searchterm2"'''
        filterforvideo = [r"&list=", r"[Clean]", r"[clean]"]
        self.driver.get("https://www.youtube.com/results?search_query="+query)
        
        try:
            confirmkey = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '''//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[4]/form/div[1]/div/button/span'''))
            )
            confirmkey.click()
        except: pass

        try:
            resultlist = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '''//*[@id="page-manager"]/ytd-search'''))
            )
        except: return False

        links = resultlist.find_elements_by_tag_name('a')

        for link in links:
            href = str(link.get_attribute('href'))
            if not href is None:
                if re.search(r"^https://www.youtube.com/watch", href):
                    if not reg_is_in_filter(filterforvideo, href):
                        return(href)
        return False

    ########################## cleanup with tuple unpacking ##############################
    def convert_playlist(self, spotify_link):
        # Get tracks and build querys
        tracklist = self.get_tracks_and_artists(spotify_link)
        
        def yt_query_from_keywords(keywords:list) -> str:
            raw_query = ' '.join(keywords)
            re_subs = [(r"&", r"+"), (r" ", r"+"), (r",", r"+"), (r"+-+", r"+"), (r"++", r"+")]
            while True:
                new_query = self.re_sub_list(raw_query, re_subs)
                if new_query == raw_query: break
                raw_query = new_query
            return new_query

        querylist = [yt_query_from_keywords(track) for track in tracklist]

        # querylist = []
        # i = 0
        # while True:
        #     try:
        #         query = tracklist[i] + " " + tracklist[i+1]
        #         query = query.replace("&", "+")
        #         query = query.replace(" ", "+")
        #         query = query.replace(",", "+")
        #         query = query.replace("+-+", "+")
        #         query = query.replace("++", "+")
        #         querylist.append(query)
        #         i += 2
        #     except: break

        # playlist_name = self.get_playlist_name(spotify_link)
        # playlist_name = playlist_name.replace("&", "and")
        # # Load progress
        # if playlist_name in self.progress_dict.keys():
        #     playlist_id = self.progress_dict[playlist_name]["playlist_id"]
        #     querys_done = self.progress_dict[playlist_name]["querys_done"]
        # else:
        #     playlist_id = self.yt_api.create_playlist(playlist_name)["id"]
        #     self.progress_dict[playlist_name] = {"playlist_id": playlist_id, "querys_done": {}}
        #     querys_done = {}
        # # Search for songs and add to playlist
        # for query in querylist:
        #     if not query in querys_done.keys():
        #         video_link = self.get_link_to_video_by_query(query)
        #         video_id = re.search(r"https://www.youtube.com/watch.v=(.*)", video_link, re.IGNORECASE).group(1)
        #         playlist_item_id = self.yt_api.add_item_to_playlist(playlist_id, video_id)["id"]
        #         querys_done[query] = playlist_item_id
        #         # Save progress
        #         self.progress_dict[playlist_name]["querys_done"] = querys_done
        #         with open(self.path_to_progress_json, 'w') as json_file:
        #             json.dump(self.progress_dict, json_file)
        # # Search for songs not longer in playlist and delete
        # for query in list(querys_done.keys()).copy():
        #     if not query in querylist: 
        #         self.yt_api.delete_item_from_playlist(querys_done[query])
        #         # Save progress
        #         querys_done.pop(query, None)
        #         with open(self.path_to_progress_json, 'w') as json_file:
        #             json.dump(self.progress_dict, json_file)
                

    def get_playlist_name(self, spotify_link):
        try:
            self.driver.get(spotify_link)
            name = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, '''a12b67e576d73f97c44f1f37026223c4-scss'''))
            )
            return name.text
        except:
            return self.get_playlist_name(spotify_link)


    def get_playlistlinks_from_profile(self, profile_link):

        self.driver.get(profile_link)
        # profileIcon = WebDriverWait(self.driver, 30).until(
        #     EC.presence_of_element_located((By.CLASS_NAME, '''_3e75c7f07bdce28b37b45a5cd74ff371-scss'''))
        # )
        # profileIcon.click()
        # profileButton = self.driver.find_element_by_xpath('''//*[@id="context-menu"]/div/ul/li[2]/a''')
        # linktext = profileButton.get_attribute('href')
        link_to_playlists = profile_link + "/playlists"
        self.driver.get(link_to_playlists)

        playlists_field = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '''//*[@id="main"]/div/div[2]/div[3]/main/div[2]/div[2]/div/div/div[2]/section/section/div[2]'''))
        )

        playlist_linklist = []
        list_link_objects = playlists_field.find_elements_by_tag_name('a')
        for item in list_link_objects:
            href = item.get_attribute('href')
            playlist_linklist.append(href)
        return playlist_linklist


    def sync_user_profile(self, profile_link):
    
        for playlist_link in self.get_playlistlinks_from_profile(profile_link):
            self.convert_playlist(playlist_link)

        


def main():

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    Yt_sptfy_converter()

if __name__ == "__main__":
    main()
# %%
