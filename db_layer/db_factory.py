import os
from dotenv import load_dotenv
from db_layer.abstract_database import AbstractDatabase
from db_layer.sql_data_service import SQLDataService
from db_layer.sqlite_database import SQLiteDatabase
from db_layer.azure_sql_database import AzureSQLDatabase
from db_layer.my_sql_database import MySQLDatabase

# Загружаем переменные окружения
load_dotenv()

def get_database() -> AbstractDatabase:
    db_type = os.getenv("DB_TYPE", "sqlite")  # По умолчанию SQLite
    if db_type == "sqlite":
        return SQLiteDatabase("database.db")
    elif db_type == "azure_sql":
        connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("Строка подключения AZURE_SQL_CONNECTION_STRING не найдена в переменных окружения.")
        return AzureSQLDatabase(connection_string)
    elif db_type == "mysql":
        host = os.getenv("MYSQL_HOST")
        port = int(os.getenv("MYSQL_PORT", 3306))
        user = os.getenv("MYSQL_USER")
        password = os.getenv("MYSQL_PASSWORD")
        database = os.getenv("MYSQL_DATABASE")
        return MySQLDatabase(host, port, user, password, database)
    else:
        raise ValueError(f"Неизвестный тип базы данных: {db_type}")

def get_data_serice():
    return SQLDataService(get_database())

