
#!.\sptfy-env\Scripts\python.exe
import sys
import pickle
import os


from google.auth.transport import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


client_secrets_path = r'client_secret.json'
credentials = None

# class yt_api:
#    '''doku: https://developers.google.com/youtube/v3/docs'''

def load_credentials():
    # token.pickle stores credentials from previously successful logins
    if os.path.exists('token.pickle'):
        print('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    else: credentials = None

    # If there are no valid credentials available, then either refresh the token or log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing Access Token...')
            try:
                credentials.refresh(Request())
            except:
                os.remove("token.pickle")
                load_credentials()
        else:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_path,
                scopes=[
                    'https://www.googleapis.com/auth/youtube'
                ]
            )
            flow.run_local_server(port=8080, prompt='consent',
                                authorization_prompt_message='')
            credentials = flow.credentials

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)

    return credentials        
    

credentials = load_credentials()
serviceYT = build("youtube", "v3", credentials=credentials)

def create_playlist(playlist_name, privacyStatus="public"):
    '''create playlist, privacyStatus can be "public" or "private"'''
    try:
        requestbody = {
            "snippet": {
                "title": str(playlist_name),
                "description": "New playlist description"
            },
            "status": {
                "privacyStatus": privacyStatus
            }
        }
        request = serviceYT.playlists().insert(
            part="snippet, status",
            body=requestbody
        )
        response = request.execute()
        return response
    except Exception as e:
        print(e)
        sys.exit()


def add_item_to_playlist(playlist_id, video_id):
    '''Add item to playlist, example:
    "https://www.youtube.com/watch?v=<playlistID>&list=<videoID>"'''
    try: 
        request = serviceYT.playlistItems().insert(
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


def delete_item_from_playlist(playlist_item_id):
    '''Remove item from playlist by id'''
    try: 
        request = serviceYT.playlistItems().delete(
            id=playlist_item_id
        )
        response = request.execute()
        return response
    except Exception as e:
        print(e)
        sys.exit()


def get_playlists(channel_id):
    '''Get playlistitem by ID, example:
    "https://www.youtube.com/channel/<channelID>" \n
    doku: https://developers.google.com/youtube/v3/docs/playlists/list'''
    try: 
        request = serviceYT.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=25,
        )
        response = request.execute()
        return response
    except Exception as e:
        print(e)
        sys.exit()


def get_user_channel():
    '''Returns the channel for the current user \n
    doku: https://developers.google.com/youtube/v3/docs/channels/list'''
    try: 
        request = serviceYT.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        return response
    except Exception as e:
        print(e)
        sys.exit()