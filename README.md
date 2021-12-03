# Spotify-Yt-Sync

This script scans spotify playlists and creates matching youtube playlists.

Also it is able to keeps track of progress and will update the created playlists => remove items

The core design of this script is to use as little api resources as posible to get around of Google quota limitation.

made in python 3.10.0

Setup:
local commands:
```powershell
# setup virtual-environment
python3 -m venv virtual-env
# install requirements in the virtual-environmen
/path/to/your/new/virtual-env/Scripts/python -m pip install -r requirements.txt
# command to start the script
/path/to/your/new/virtual-env/Scripts/python convert.py
```
additional steps:
https://www.youtube.com/watch?v=HzICUriU3k0&ab_channel=JieJenn

Add links for profiles or playlists to be converted in config.ini


SQL schema:

![Alt text](sql_schema.png?raw=true "SQL schema")



Do not change the windowsize for chromedriver


For now, login information for spotify is not required, just leave config undefinded


TODO:
 - add filter for songnames
 - add terminal controller
 - allow for manual correction of videos (will need to restructure sqlite for this probably)