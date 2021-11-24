import sqlite3
from sqlite3 import Error
from sqlite3.dbapi2 import Connection
import logging


class Sqlite_handler():

    def __init__(self) -> None:

        self.logger = logging.getLogger(__name__)
        self.path_to_database: str = "progress.sqlite"
        self.conn: Connection = self.load_database(self.path_to_database)


    def load_schema(self, path:str) -> dict:
        return

    def load_database(self, path:str) -> Connection:
        connection = None
        try:
            connection = sqlite3.connect(path)
            self.logger.info("Connection to SQLite DB successful")
        except Error as err:
            self.logger.error(f"{err}' occurred while connecting to {path=}")
        return connection

    def close_conn(self):
        self.conn.commit()
        self.conn.close()


    def q_exec(self, query: str):
        return self.conn.execute(query)

    def q_(self, query: str):
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def reset_tables():
        pass


sql = Sqlite_handler()
sql.q_exec('''CREATE TABLE PLAYLISTS (
    ID INT PRIMARY KEY NOT NULL,
    NAME VARCHAR(100) NOT NULL,
    CREATOR VARCHAR(100) NULL,
    SPOTIFY_LINK VARCHAR(100) NOT NULL);''')
sql.close_conn()


        