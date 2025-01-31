import mysql.connector  # Для MySQL

from db_layer.abstract_database import AbstractDatabase


class MySQLDatabase(AbstractDatabase):
    def __init__(self, host, database, username, password):
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database=self.database
        )

    def execute_query(self, query: str, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        self.connection.commit()

    def fetch_all(self, query: str, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()
