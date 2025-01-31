import pyodbc  # Для Azure SQL

from db_layer.abstract_database import AbstractDatabase


class AzureSQLDatabase(AbstractDatabase):
    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        self.connection = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password}'
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


class MySQLDatabase(AbstractDatabase):
    def __init__(self, host, database, username, password):
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.connection = None