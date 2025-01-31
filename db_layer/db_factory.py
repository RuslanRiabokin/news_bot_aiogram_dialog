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
        return AzureSQLDatabase("azure_connection_string")
    elif db_type == "mysql":
        return MySQLDatabase("mysql_connection_string")
    else:
        raise ValueError(f"Неизвестный тип базы данных: {db_type}")

def get_data_serice():
    return SQLDataService(get_database())

