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

    
    def create_table_query_from_dict(self, schema:dict) -> str:
        name = next(iter(schema))
        columns = schema[name]
        column_querys = ", ".join([f"{key} {struct}" for key, struct in columns.items()])
        return  f"CREATE TABLE {name}({column_querys});"


    def q_exec(self, query: str):
        return self.conn.execute(query)

    def q_(self, query: str):
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()


# sql = Sqlite_handler()
# test = {
#   "PLAYLISTS":{
#     "ID": "INT PRIMARY KEY NOT NULL",
#     "NAME": "VARCHAR(100) NOT NULL",
#     "CREATOR": "VARCHAR(100)",
#     "SPOTIFY_LINK": "VARCHAR(100)"}}

# sql.q_exec(sql.create_table_query_from_dict(test))

# sql.close_conn()


        