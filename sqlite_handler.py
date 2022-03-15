import sqlite3
from sqlite3 import Error
from sqlite3.dbapi2 import Connection, Cursor
import logging
import sys
from typing import Iterable
import yaml
from yaml.error import YAMLError

import read_yaml 


class Sqlite_handler():

    def __init__(self, database_file:str = "progress.sqlite") -> None:

        self.logger = logging.getLogger(__name__)
        self.conn: Connection = self.load_database(database_file)

        self.create_db_from_yml("sqlite_schema.yml")


    def create_db_from_yml(self, file_path: str) -> None:
        yaml_dict = read_yaml.read_yml_file(file_path)
        for tablename, schema in yaml_dict.items():
            self.create_table_from_schema(tablename, schema)


    def create_table_from_schema(self, tablename: str, schema: dict[str, str]) -> None:
        if self.get_entry_count(f"type='table' AND name='{tablename}'"):
            self.logger.info(f"did not create {tablename}, already present")
            return
        column_querys = ", ".join([f"{key} {struct}" for key, struct in schema.items()])
        self.q_exec(f"CREATE TABLE {tablename} ({column_querys});")
        self.conn.commit()


    def get_entry_count(self, condition:str, table_name:str="sqlite_master", sqlvars:tuple=()) -> int:
        query = f'''SELECT count(*) FROM {table_name} WHERE {condition};'''
        cursor = self.q_exec(query, sqlvars)
        return cursor.fetchone()[0]


    def load_database(self, path:str) -> Connection:
        connection = None
        try:
            connection = sqlite3.connect(path)
            self.logger.info("Connection to SQLite DB successful")
        except Exception as err:
            self.logger.error(f"{err}' occurred while connecting to {path=}")
        return connection


    def close_conn(self) -> None:
        self.conn.commit()
        self.conn.close()


    def q_exec(self, query: str, args: tuple = ()) -> Cursor:
        cursor = self.conn.cursor()
        self.logger.info(f"{query=} {args=}")
        cursor.execute(query, args)
        self.conn.commit()
        return cursor


    def q_exec_many(self, query: str, iter_params: Iterable) -> Cursor:
        cursor = self.conn.cursor()
        self.logger.info(f"{query=}, {iter_params=}")
        cursor.executemany(query, iter_params)
        self.conn.commit()
        return cursor


if __name__ == "__main__":
    db = Sqlite_handler()
