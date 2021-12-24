
#!.\sp_yt_env\Scripts\python.exe
import sys
import pickle
import os
import logging
from typing import Optional


from google.auth.transport import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Yt_api:
    '''doku: https://developers.google.com/youtube/v3/docs'''

    def __init__(self) -> None:
        
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


    def list_playlist(self, playlist_id: str) -> Optional[dict]:
        '''list playlist, found by id \n
        doku: https://developers.google.com/youtube/v3/docs/playlists/list'''
        try:
            request = self.serviceYT.playlists().list(
                part = "contentDetails, id, localizations, player, snippet, status",
                id = playlist_id
            )
            return request.execute()
        except Exception as err:
            logging.error(err)
            return False


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
            return request.execute()
        except Exception as e:
            logging.error(e)
            return False


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
            return request.execute()
        except Exception as e:
            logging.error(e)
            return False


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
            response = request.execute()
            return response
        except Exception as e:
            print(e)
            sys.exit()


    def delete_item_from_playlist(self, playlist_item_id):
        '''Remove item from playlist by id \n
        doku: https://developers.google.com/youtube/v3/docs/playlistItems/delete'''
        try: 
            request = self.serviceYT.playlistItems().delete(
                id=playlist_item_id
            )
            response = request.execute()
            return response
        except Exception as e:
            print(e)
            sys.exit()


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
            response = request.execute()
            return response
        except Exception as e:
            print(e)
            sys.exit()


    def get_user_channel(self):
        '''Returns the channel for the current user \n
        doku: https://developers.google.com/youtube/v3/docs/channels/list'''
        try: 
            request = self.serviceYT.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            return response
        except Exception as e:
            print(e)
            sys.exit()
