import sqlite3
from sqlite3 import Error
from sqlite3.dbapi2 import Connection
import logging


class Sqlite_handler():

    def __init__(self) -> None:
        pass

        self.path_to_database: str = "progress.sqlite"


    def load_database(self, path:str) -> Connection:
        connection = None
        try:
            connection = sqlite3.connect(path)
            print("Connection to SQLite DB successful")
        except Error as err:
            logging.error(f"The error '{err}' occurred")
        return connection

        