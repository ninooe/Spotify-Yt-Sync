import sqlite3
from sqlite3 import Error
from sqlite3.dbapi2 import Connection, Cursor
import logging
import sys
import yaml


class Sqlite_handler():

    def __init__(self, database_file:str = "progress.sqlite") -> None:

        self.logger = logging.getLogger(__name__)
        self.conn: Connection = self.load_database(database_file)

        self.sql_schema = self.load_schema("sqlite_schema.yaml")
        if not self.table_exists("PLAYLISTS"):
            self.create_table_from_preset("PLAYLISTS", "PLAYLISTS")

        
    # def add_cursor(func):s
    #     def wrap(self, *args, **kwargs) :
    #         with self.conn.cursor() as cursor:
    #             kwargs["cursor"] = cursor
    #             return func(self,  *args, **kwargs)
    #     return wrap

    def table_exists(self, table_name) -> bool:
        cursor = self.q_exec(f'''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}';''')
        if cursor.fetchone()[0]==1: 
            return True
        return False

    def load_schema(self, path:str) -> dict:
        with open(path, "r") as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    def load_database(self, path:str) -> Connection:
        connection = None
        try:
            connection = sqlite3.connect(path)
            self.logger.info("Connection to SQLite DB successful")
        except Exception as err:
            self.logger.error(f"{err}' occurred while connecting to {path=}")
        return connection

    def close_conn(self):
        self.conn.commit()
        self.conn.close()

    
    def create_table_from_preset(self, preset:str, tablename:str) -> str:
        columns = self.sql_schema['TABLES'][preset]
        column_querys = ", ".join([f"{key} {struct}" for key, struct in columns.items()])
        self.conn.execute(f"CREATE TABLE {tablename}({column_querys});")
        self.conn.commit()

    def q_exec(self, query: str):
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        return cursor


        