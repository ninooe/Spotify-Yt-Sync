
#!.\sp_yt_env\Scripts\python.exe
import sys
import pickle
import os
import logging
from typing import Optional
from urllib import response
import time
import inspect

from google.auth.transport import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def retry_if_no_response(func):
    '''retry decorator for Yt_api class'''    
    def check_response(*args, **kwargs):
        if not args[0].numb_of_retrys or not args[0].wait_till_retry:
            return func(*args, **kwargs)
        for _ in range(args[0].numb_of_retrys):
            if (resp := func(*args, **kwargs)):
                return resp
        time.sleep(args[0].wait_till_retry)
    return check_response


class Yt_api:
    '''doku: https://developers.google.com/youtube/v3/docs'''

    def __init__(self) -> None:
        
        # used by the retry_if_no_response decorator
        self.numb_of_retrys = 5
        self.wait_till_retry = 10
        
        self.client_secrets_path = r'client_secret.json'
        self.path_to_token = "token.pickle"
        self.logger = logging.getLogger(__name__)

        self.serviceYT = build("youtube", "v3", credentials=self.load_credentials())


    def load_credentials(self):

        def credentials_from_file(path:str):
            self.logger.info('Loading Credentials From File...')
            if not os.path.exists(path):
                return None
            with open(path, 'rb') as token:
                # token.pickle stores credentials from previously successful logins
                return pickle.load(token)

        credentials = credentials_from_file(self.path_to_token)

        # If there are no valid credentials available, then either refresh the token or log in.
        if credentials and credentials.valid:
            return credentials
         # if credentials present try to loading, if this failes delete and retry
        if credentials:
            self.logger.info('Refreshing Access Token...')
            try:
                credentials.refresh(Request())
            except Exception as error:
                self.logger.info(f"{error=} while loading {self.path_to_token}, removing before retry")
                os.remove(self.path_to_token)
                return self.load_credentials()


        self.logger.info('Fetching New Tokens...')
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_path,
            scopes=[
                'https://www.googleapis.com/auth/youtube'
            ]
        )
        flow.run_local_server(port=8080, prompt='consent',
                            authorization_prompt_message='')
        credentials = flow.credentials

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as f:
            self.logger.info('Saving Credentials for Future Use...')
            pickle.dump(credentials, f)

        return credentials   


    @retry_if_no_response
    def list_video(self, video_id: str) -> Optional[dict]:
        '''list video, found by id \n
        doku: https://developers.google.com/youtube/v3/docs/videos/list \n
        video_id can be a comma-seperated list to get multiple results'''
        try:
            request = self.serviceYT.videos().list(
                part = "snippet, contentDetails",
                id = video_id
            )   
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as err:
            self.logger.error(err)


    @retry_if_no_response
    def list_playlist(self, playlist_id: str) -> Optional[dict]:
        '''list playlist, found by id \n
        doku: https://developers.google.com/youtube/v3/docs/playlists/list'''
        try:
            request = self.serviceYT.playlists().list(
                part = "contentDetails, id, localizations, player, snippet, status",
                id = playlist_id
            )
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as err:
            self.logger.error(err)


    @retry_if_no_response
    def create_playlist(self, playlist_name, privacyStatus="public"):
        '''create playlist, privacyStatus can be "public" or "private" \n
        doku: https://developers.google.com/youtube/v3/docs/playlists/insert'''
        requestbody = {
            "snippet": {
                "title": str(playlist_name),
                "description": "New playlist description"
            },
            "status": {
                "privacyStatus": privacyStatus
            }
        }
        try:
            request = self.serviceYT.playlists().insert(
                part="snippet, status",
                body=requestbody
            )
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as e:
            self.logger.error(e)


    @retry_if_no_response
    def update_playlist(self, playlist_id: str, priv_status: str = None, snippet: dict = None):
        '''update playlist, privacyStatus can be "public" or "private" \n
        doku: https://developers.google.com/youtube/v3/docs/playlists/update'''
        requestbody = {"id": playlist_id}
        if priv_status: requestbody["status"] = priv_status
        requestbody["snippet"] = {}
        if snippet: requestbody["snippet"] = snippet
        try:
            request = self.serviceYT.playlists().update(
                part="snippet, status",
                body=requestbody
            )
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as e:
            self.logger.error(e)


    @retry_if_no_response
    def add_item_to_playlist(self, playlist_id, video_id) -> dict:
        '''Add item to playlist, example:
        "https://www.youtube.com/watch?v=<playlistID>&list=<videoID>" \n
        doku: https://developers.google.com/youtube/v3/docs/playlistItems/insert'''
        try: 
            request = self.serviceYT.playlistItems().insert(
                part="snippet, status",
                body={
                "snippet": {
                        "playlistId": playlist_id,
                        "position": 0,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as e:
            self.logger.error(e)


    @retry_if_no_response
    def delete_item_from_playlist(self, playlist_item_id):
        '''Remove item from playlist by id \n
        doku: https://developers.google.com/youtube/v3/docs/playlistItems/delete'''
        try: 
            request = self.serviceYT.playlistItems().delete(
                id=playlist_item_id
            )
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as e:
            self.logger.error(e)


    @retry_if_no_response
    def get_playlists(self, channel_id):
        '''Get playlistitem by ID, example:
        "https://www.youtube.com/channel/<channelID>" \n
        doku: https://developers.google.com/youtube/v3/docs/playlists/list'''
        try: 
            request = self.serviceYT.playlists().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=25,
            )
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as e:
            self.logger.error(e)


    @retry_if_no_response
    def get_user_channel(self):
        '''Returns the channel for the current user \n
        doku: https://developers.google.com/youtube/v3/docs/channels/list'''
        try: 
            request = self.serviceYT.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            resp = request.execute()
            self.logger.debug(f"{inspect.stack()[0][3]} with {locals().items()} returned {resp}")
            return resp
        except Exception as e:
            self.logger.error(e)

