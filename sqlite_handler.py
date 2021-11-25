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
        if not self.entry_exists("type='table' AND name='Playlists'"):
            self.create_table_from_preset("Playlists", "Playlists")


    def entry_exists(self, condition:str, table_name:str="sqlite_master") -> bool:
        query = f'''SELECT count(name) FROM {table_name} WHERE {condition};'''
        cursor = self.q_exec(query)
        if cursor.fetchone()[0]==1: 
            return True
        return False    

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
        columns = self.sql_schema['Tables'][preset]
        column_querys = ", ".join([f"{key} {struct}" for key, struct in columns.items()])
        self.conn.execute(f"CREATE TABLE {tablename}({column_querys});")
        self.conn.commit()

    def q_exec(self, query: str):
        cursor = self.conn.cursor()
        self.logger.error(f"{query=}")
        cursor.execute(query)
        self.conn.commit()
        return cursor

    def q_exec_many(self, query: str, iter_params:Iterable):
        cursor = self.conn.cursor()
        self.logger.error(f"{query=}, {iter_params=}")
        cursor.executemany(query, iter_params)
        self.conn.commit()
        return cursor

        