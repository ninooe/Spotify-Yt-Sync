#! sfyt-env\Scripts\python.exe
from typing import Optional
from prettytable import PrettyTable
import msvcrt
import logging
import sys
import inspect
import re
from convert import *

###################### not functional by now wip ####################################
class Terminal_controller():

    def __init__(self, converter: Yt_sptfy_converter):
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename='terminal_menu.log', encoding='utf-8', level=logging.INFO)

        self.conv = converter

        print('TERMINAL CONTROLLER')
        
        self.main_menu()

    
    def menu_loop(self, options: list[tuple,], msg: Optional[str] = None):
        # will add option for helptext matching parent function
        options.append(("[H]elp", self.help_text, (str(inspect.stack()[1][3]),)))
        options.append(("[E]xit", sys.exit))
        while True:
            if msg: 
                print(msg)
            print("Options:")
            print(", ".join([opt[0] for opt in options]))
            keyreg = re.compile(r"\[(.)\]")
            opt = {keyreg.match(tup[0])[1]: tup for tup in options}
            command = msvcrt.getch().decode('utf-8').upper()
            try:
                tup = opt[command]
                if len(tup) == 2: tup[1]()
                elif len(tup) == 3: tup[1](*tup[2])
                elif len(tup) == 4: tup[1](*tup[2], **tup[3])
            except Exception as err:
                print(f"{err=} occured")
                self.logger.error(err)


    def main_menu(self):
        options = [
            ("[S]ync_Playlists(Youtube)", (self.sync_playlists,)),
            ("[I]mport_link(Spotify)", (self.import_link,)),
            ("[L]ookup_database", (self.import_link,))
        ]
        self.menu_loop(options)

    
    def database_menu(self):
        selections = [
            ("[E]xit", sys.exit)
        ]
        self.menu_loop(selections)


    @staticmethod
    def help_text(functionname: str):
        match functionname:
            case "main_menu":
                print("this")
            case _:
                print("Press the key in Brackets to chose described option -> []")
                print("this helptext might be more usefull in another menus")
        


    def sync_playlists(self):
        print("Syncing playlists in db to youtube")
        print("Programm will exit when quota are depleted")
        tab = PrettyTable(['ID', 'name', 'creator', 'spotify_link'])
        tab.add_rows([res[:] for res in self.conv.sql.q_exec('SELECT ID, name, creator, sp_link FROM Playlists').fetchall()])
        print(tab)
        inp = input('enter ID of playlist to sync, or [A]ll (confirm with enter)\n')
        keys = [inp]
        if inp.upper() in ["A", "ALL"]:
            keys = [pk[0] for pk in self.conv.sql.q_exec(f"SELECT ID FROM Playlists").fetchall()]
        list(map(self.conv.update_playlist, keys))
        print("DONE\n")

    def import_link(self):
        link = input('paste spotify link playlist/profile (confirm with enter)\n')
        affected_links = self.conv.import_link(link)                
        for link in affected_links:
            self.conv.update_playlist_info(link)
            print("Done:", self.conv.sql.q_exec(f'SELECT ID, name, creator, sp_link FROM Playlists WHERE sp_link = ?', (link)).fetchone()[0])
        print("\n")

        


def main():
    Terminal_controller(Yt_sptfy_converter())

if __name__ == "__main__":
    main()