# Spotify-Yt-Sync

This script scans spotify playlists and creates matching youtube playlists.

Also it is able to keeps track of progress and will update the created playlists => remove items

The core design of this script is to use as little api resources as posible to get around of Google quota limitation.

made in python 3.10.0

Setup:
local commands:
```powershell
# setup virtual-environment
python3 -m venv /path/to/your/new/virtual-env
# install requirements in the virtual-environmen
/path/to/your/new/virtual-env/Scripts/python -m pip install -r /path/to/requirements.txt
# command to start the script
/path/to/your/new/virtual-env/Scripts/python /path/to/convert.py
```
additional steps:
https://www.youtube.com/watch?v=HzICUriU3k0&ab_channel=JieJenn

Add links for profiles or playlists to be converted in config.ini



Do not change the windowsize for chromedriver


For now, login information for spotify is not required, just leave config undefinded


TODO:
- Change names of playlist
