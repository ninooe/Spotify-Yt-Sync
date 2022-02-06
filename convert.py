
#! sfyt-env\Scripts\python.exe
from ast import keyword
import datetime
from inspect import _void
from urllib.parse import quote

import os
import sys
import re
import time
import logging
from pyparsing import nullDebugAction


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

## usefull links ##
# https://spotipy.readthedocs.io/en/2.19.0/#features

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
        
        self.test()

        self.convert_links_in_config()
        
    def test(self):

        # print(self.spty_api.track(self.sql.q_exec("SELECT sp_id FROM track WHERE ID = 1").fetchone()[0]))
        # print(self.spotify_ids_from_link("https://open.spotify.com/user/eo81sypyqdkath705ozd16yzh"))
        
        self.import_playlist_from_spotify("5mxDiK1jscv6V0EtYdRp0z")
        # self.get_yt_id_playlist("5mxDiK1jscv6V0EtYdRp0z")
        # print(self.supplement_yt_ids())
        self.insert_videos_to_playlists()
        # print(self.update_playlist_name("0CEj2EbTgWaCtYppgJwtQe"))
        sys.exit()

    @staticmethod
    def link2id(link):
        '''works for any spotify and youtube link'''
        link = re.search(r"\/([^/]+)$", link)[1]
        if (match := re.search(r"watch\?v=([a-zA-Z0-9-_]+)", link)):
            link = match[1]
        return re.search(r"^([a-zA-Z0-9-_]+)", link)[1]
  

    # read information from spotify        
    def get_playlists_from_user(self, sp_id) -> list[str]:
        playlist_ids = []
        api_result = self.spty_api.user_playlists(sp_id)
        while api_result:
            for item in api_result["items"]:
                playlist_ids.append(item["id"])
            if api_result['next']:
                api_result = self.spty_api.next(api_result)
            else:
                api_result = None
        return playlist_ids


    def add_artist(self, sp_id: str, name: str = None) -> int:
        if (id := self.sql.q_exec("SELECT ID FROM artist WHERE sp_id=?", (sp_id,)).fetchone()):
            return id[0]
        if not name:
            name = self.spty_api.artist(sp_id)["name"]
        return self.sql.q_exec('INSERT INTO artist (sp_id, name) VALUES (?, ?)', (sp_id, name)).lastrowid


    def add_track(self, sp_id: str, name: str = None, artist_ids: list = None) -> int:
        if (id := self.sql.q_exec("SELECT ID FROM track WHERE sp_id=?", (sp_id,)).fetchone()):
            return id[0]
        if not name or not artist_ids:
            api_result = self.spty_api(sp_id)
            name = api_result["name"]
            artist_ids = [aid["id"] for aid in api_result["artists"]]
        track_id = self.sql.q_exec('INSERT INTO track (sp_id, name) VALUES (?, ?)', (sp_id, name)).lastrowid
        [self.link_artist_to_track(aid, track_id) for aid in artist_ids]
        return track_id


    def add_playlist(self, sp_id: str, name: str = None) -> int:
        if (resp := self.sql.q_exec("SELECT ID, name FROM playlist WHERE sp_id=?", (sp_id,)).fetchone()):
            return resp[0]
        if not name:
            name = self.spty_api.playlist(sp_id)["name"]
        return self.sql.q_exec('INSERT INTO playlist (sp_id, name) VALUES (?, ?)', (sp_id, name)).lastrowid

        
    def link_artist_to_track(self, artist_id: str, track_id: str) -> None:
        if self.sql.q_exec("SELECT * FROM artist_track_mn WHERE track_id=? AND artist_id=?", (track_id, artist_id)).fetchone():
            return
        self.sql.q_exec("INSERT INTO artist_track_mn (track_id, artist_id) VALUES (?, ?)", (track_id, artist_id))
    
        
    def link_playlist_to_track(self, playlist_id: str, track_id: str) -> None:
        if self.sql.q_exec("SELECT * FROM playlist_track_mn WHERE track_id=? AND playlist_id=?", (track_id, playlist_id)).fetchone():
            return
        self.sql.q_exec("INSERT INTO playlist_track_mn (track_id, playlist_ID) VALUES (?, ?)", (track_id, playlist_id))
        

    def unlink_playlist_from_track(self, track_id: str, playlist_id: str) -> None:
        self.sql.q_exec(f"DELETE FROM playlist_track_mn WHERE track_id = ? AND playlist_ID = ?", (track_id, playlist_id))


    def playlist_name_from_spotify(self, playlist_id: str) -> str:
        name = self.spty_api.playlist(playlist_id, fields=("name",))["name"]
        self.sql.q_exec(f"UPDATE playlist SET name = ? WHERE sp_link = ?", (name, playlist_id))
        return name


    # write information to youtube
    def sync_playlist_name_sp2yt(self, playlist_id: str) -> None:
        yt_id = self.sql.q_exec("SELECT yt_ID FROM playlist where sp_id = ?", (playlist_id,)).fetchone()
        playlist_name = self.playlist_name_from_spotify(playlist_id)
        if not self.yt_api.list_playlist(yt_id)["items"][0]["snippet"]["localized"]["title"] == playlist_name:
            self.yt_api.update_playlist(yt_id, snippet={"title": playlist_name})


    # read information from youtube
    def get_yt_title(self, yt_ids: list[str]) -> Optional[list[str]]:
        yt_ids = ",".join(yt_ids)
        return [item["snippet"]["title"] for item in self.yt_api.list_video(yt_ids)["items"]]


    def import_playlist_from_spotify(self, sp_id):
        # get information from spotify api
        playlist_items = []
        api_result = self.spty_api.playlist_items(sp_id, additional_types=("track",))
        while api_result:
            for item in api_result["items"]:
                artists = [{"name": artist["name"], "sp_id": artist["id"]} for artist in item["track"]["artists"]]
                # add artists to db if not present and get id
                artist_ids = [self.add_artist(**k) for k in artists]
                playlist_items.append({
                    "name": item["track"]["name"],
                    "sp_id": item["track"]["id"],
                    "artist_ids": artist_ids
                })
            if api_result['next']:
                api_result = self.spty_api.next(api_result)
            else:
                api_result = None 
        # add tracks to database
        track_ids = [self.add_track(**k) for k in playlist_items]
        playlist_id = self.add_playlist(sp_id, )
        [self.link_playlist_to_track(playlist_id, tid) for tid in track_ids]


    def get_yt_id_playlist(self, playlist_id) -> str:
        """gets yt_id for playlist from DB, creates playlist if not present"""
        yt_id, name = self.sql.q_exec('SELECT yt_id, name FROM playlist WHERE sp_id=?', (playlist_id,)).fetchone()
        if not name: 
            self.playlist_name_from_spotify(playlist_id)
        if not yt_id:
            yt_id = self.yt_api.create_playlist(name)["id"]
            self.sql.q_exec('UPDATE playlist SET yt_id=? WHERE sp_id=?', (yt_id, playlist_id))
        return yt_id


    def yt_query_from_id(self, id: str) -> str:

        artist_ids = tuple(res[0] for res in self.sql.q_exec("SELECT artist_id FROM artist_track_mn WHERE track_id=?", (id,)).fetchall())
        name = self.sql.q_exec("SELECT name FROM track WHERE ID=?", (id,)).fetchone()[0]
        if not artist_ids:
            logging.error(f"no artists found for track_{id=}")
            return quote(name)
        if len(artist_ids) == 1:
            keywords = [self.sql.q_exec("SELECT name FROM artist WHERE ID=?", (artist_ids[0],)).fetchone()[0]]
        else:
            keywords = [res[0] for res in self.sql.q_exec(f"SELECT name FROM artist WHERE ID IN {artist_ids}").fetchall()]
        keywords.append(name)
        return quote("+".join(keywords))
    
    
    def get_yt_id_and_title_from_query(self, query: str) -> Optional[tuple[str, str]]:
        '''query must be sanitized for url'''
        self.driver.get(f"https://www.youtube.com/results?search_query={query}")
        
        filter_for = ["clean"]
        filter_for = [ff for ff in filter_for if not re.match(ff, query, re.IGNORECASE)]

        if not (resultlist := wait_for_element(By.XPATH, '''//*[@id="page-manager"]/ytd-search''', self.driver, timeout=30)):
            return False
        hrefs = [link.get_attribute('href') for link in resultlist.find_elements(By.TAG_NAME, 'a')]
        hrefs = [str(href) for href in hrefs if href]
        yt_ids = [self.link2id(href) for href in hrefs if re.match(r"^https://www.youtube.com/watch", href)]
        yt_ids = list(dict.fromkeys(yt_ids))
        yt_titles = self.get_yt_title(yt_ids)
        for id, title in zip(yt_ids, yt_titles):
            for ff in filter_for:
                if re.match(ff, title):
                    continue
            return id, title
        self.logger.error(f"no video found for {query=}")
        return False


    def get_yt_id_track(self, id: str | int) -> tuple[str, str]:
        query = self.yt_query_from_id(id)
        return self.get_yt_id_and_title_from_query(query)
    
    
    def supplement_yt_ids(self) -> None:
        cur = self.sql.q_exec("SELECT ID FROM track WHERE yt_id IS NULL").fetchall()
        idtt = [(self.get_yt_id_track(res[0]), res[0]) for res in cur]
        idtt_parsed = [(ii[0], ii[1], ee) for ii, ee in idtt]
        self.sql.q_exec_many("UPDATE track SET yt_id=?, yt_title=? WHERE ID=?", idtt_parsed)


    def spotify_ids_from_link(self, spotify_link: str) -> list[str]:
        if re.search(r"https://open.spotify.com/playlist/", spotify_link):
            return [self.link2id(spotify_link)]
        if re.search(r"https://open.spotify.com/user/", spotify_link):
            return self.get_playlists_from_user(self.link2id(spotify_link))
        logging.info(f'{spotify_link} did not match user or playlist regex')


    def import_links_in_config(self) -> None:
        links = [self.config["sync_links"][entry] for entry in self.config["sync_links"]]
        ids = [self.spotify_ids_from_link(link) for link in links]
        # merge lists
        ids = [jj for subl in ids for jj in subl]
        [self.import_playlist_from_spotify(pl_id) for pl_id in ids]
        
        
    def insert_videos_to_playlists(self):
        cur = self.sql.q_exec("SELECT playlist_id, track_id FROM playlist_track_mn WHERE yt_id IS NULL").fetchall()
        for pid, tid in cur:
            t_yt_id = self.sql.q_exec("SELECT yt_id FROM track WHERE ID=?", (tid,)).fetchone()[0]
            p_yt_id = self.sql.q_exec("SELECT yt_id FROM playlist WHERE ID=?", (pid,)).fetchone()[0]
            if not t_yt_id or not p_yt_id:
                continue
            yt_id = self.yt_api.add_item_to_playlist(p_yt_id, t_yt_id)
            if not yt_id:
                sys.exit(0)
            self.sql.q_exec("UPDATE playlist_track_mn SET yt_id=? WHERE track_id=? AND playlist_id=?", (yt_id, tid, pid))
            
            
            
            
        # # update playlistnames in db
        # list(map(self.update_playlist_info, ids))
        # for link in ids:
        #     id = self.update_playlist(link)
        #     # self.sync_tracks_yt(id)


def main():

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    Yt_sptfy_converter()

if __name__ == "__main__":
    main()