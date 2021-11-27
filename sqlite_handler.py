import sqlite3
from sqlite3 import Error
from sqlite3.dbapi2 import Connection, Cursor
import logging
import sys
from typing import Iterable
import yaml
from yaml.error import YAMLError


class Sqlite_handler():

    def __init__(self, database_file:str = "progress.sqlite") -> None:

        self.logger = logging.getLogger(__name__)
        self.conn: Connection = self.load_database(database_file)

        self.sql_schema = self.load_schema("sqlite_schema.yaml")
        # create default tables if not present
        self.create_table_from_preset("Playlists", "Playlists")


    def get_entry_count(self, condition:str, table_name:str="sqlite_master") -> int:
        query = f'''SELECT count(*) FROM {table_name} WHERE {condition};'''
        cursor = self.q_exec(query)
        return cursor.fetchone()[0]

    def fetchall(self, values:str = "*", table_name:str="sqlite_master", condition:str=None) -> list[tuple]:
        query = f'''SELECT {values} FROM {table_name}{f' WHERE {condition};' if condition else ';'}'''
        cursor = self.q_exec(query)
        return cursor.fetchall()

    def load_schema(self, path:str) -> dict:
        with open(path, "r") as file:
            try:
                return yaml.load(file, Loader=yaml.FullLoader)
            except (YAMLError):
                self.logger.error(f'failed to load yaml {path=}')

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
        if self.get_entry_count(f"type='table' AND name='{tablename}'"):
            self.logger.info(f"did not create {tablename}, already present")
            return
        columns = self.sql_schema['Tables'][preset]
        column_querys = ", ".join([f"{key} {struct}" for key, struct in columns.items()])
        self.q_exec(f"CREATE TABLE {tablename} ({column_querys});")
        self.conn.commit()

    def q_exec(self, query: str, args=None):
        cursor = self.conn.cursor()
        self.logger.info(f"{query=}")
        if args:
            cursor.execute(query, args)
        else:
            cursor.execute(query)
        self.conn.commit()
        return cursor

    def q_exec_many(self, query: str, iter_params:Iterable):
        cursor = self.conn.cursor()
        self.logger.info(f"{query=}, {iter_params=}")
        cursor.executemany(query, iter_params)
        self.conn.commit()
        return cursor

        