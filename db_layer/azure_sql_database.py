import logging
from db_layer.abstract_database import AbstractDatabase
import pyodbc

logging.basicConfig(level=logging.INFO)


class AzureSQLDatabase(AbstractDatabase):
    """Класс для работы с Azure SQL."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None

    async def connect(self):
        """Подключение к Azure SQL."""
        try:
            if not self.connection_string:
                raise ValueError("The connection string is empty.")

            logging.info(f"Attempting to connect to Azure SQL using connection string: {self.connection_string}")

            self.connection = pyodbc.connect(self.connection_string, autocommit=True)
            logging.info("Connection to Azure SQL established successfully.")
        except pyodbc.Error as db_exc:
            logging.error("Database-specific error occurred while connecting to Azure SQL: %s", db_exc, exc_info=True)
        except Exception as exc:
            logging.error("Unexpected error occurred while connecting to Azure SQL: %s", exc, exc_info=True)

    async def disconnect(self):
        """Отключение от Azure SQL."""
        if self.connection:
            try:
                self.connection.close()
                logging.info("Azure SQL connection closed successfully.")
            except Exception as exc:
                logging.error("Failed to close Azure SQL connection. Details: %s", exc, exc_info=True)

    async def execute(self, query: str, params: tuple = ()):
        """Выполнение SQL-запроса."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            cursor.execute("SELECT @@IDENTITY")
            lastrowid = cursor.fetchone()[0]
            self.connection.commit()
            return lastrowid
        except Exception as exc:
            logging.error("Error executing SQL query. Details: %s", exc, exc_info=True)

    async def fetchone(self, query: str, params: tuple = ()):
        """Получение одного результата из Azure SQL."""
        if not self.connection:
            logging.error("Fetchone error: No active connection to Azure SQL.")
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as exc:
            logging.error("Fetchone error in Azure SQL. Query: %s, Params: %s, Details: %s", query, params, exc,
                          exc_info=True)
            return None

    async def fetchall(self, query: str, params: tuple = ()):
        """Получение всех результатов."""
        if not self.connection:
            logging.error("Fetchall error: No active connection to Azure SQL.")
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as exc:
            logging.error("Fetchall error in Azure SQL. Query: %s, Params: %s, Details: %s", query, params, exc,
                          exc_info=True)
            return None


    """async def create_tables(self):
        #Создание таблиц.
        try:
            await self.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'News')
        BEGIN
            CREATE TABLE News (
                id INT IDENTITY(1,1) PRIMARY KEY,
                topic_name NVARCHAR(MAX) NOT NULL,
                channel_name NVARCHAR(255) NOT NULL,
                channel_url NVARCHAR(MAX) NOT NULL,
                last_pub_time NVARCHAR(255) NOT NULL,
                user_id NVARCHAR(255) NOT NULL,
                news_type NVARCHAR(255) NOT NULL,
                publish_frequency NVARCHAR(255) NOT NULL,
                language_code NVARCHAR(255) NOT NULL,
                add_poll NVARCHAR(255) NOT NULL,
                is_active BIT NOT NULL,  -- Логічний тип (0 або 1)
                poll_text NVARCHAR(MAX) NOT NULL
            );
        END;
            ''')
            await self.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Publish_date')
        BEGIN
            CREATE TABLE Publish_date (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sub_id INT NOT NULL,
                pub_time NVARCHAR(255) NOT NULL,
                FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
            );
        END;
            ''')
            await self.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Publish_time')
        BEGIN
            CREATE TABLE Publish_time (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sub_id INT NOT NULL,
                pub_time NVARCHAR(255) NOT NULL,
                sended INT NOT NULL DEFAULT 0,
                FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
            );
        END;
            ''')
        except Exception as e:
            logging.error(f"Error creating tables in Azure SQL: {e}")"""

    async def create_tables(self):
        """Создание таблиц в базе данных."""
        create_queries = [
            '''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'News')
            BEGIN
                CREATE TABLE News (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    topic_name NVARCHAR(MAX) NOT NULL,
                    channel_name NVARCHAR(255) NOT NULL,
                    channel_url NVARCHAR(MAX) NOT NULL,
                    last_pub_time NVARCHAR(255) NOT NULL,
                    user_id NVARCHAR(255) NOT NULL,
                    news_type NVARCHAR(255) NOT NULL,
                    publish_frequency NVARCHAR(255) NOT NULL,
                    language_code NVARCHAR(255) NOT NULL,
                    add_poll NVARCHAR(255) NOT NULL,
                    is_active NVARCHAR(15) NOT NULL,
                    poll_text NVARCHAR(MAX) NOT NULL
                );
            END;
            ''',
            '''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Publish_date')
            BEGIN
                CREATE TABLE Publish_date (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    sub_id INT NOT NULL,
                    pub_time NVARCHAR(255) NOT NULL,
                    FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
                );
            END;
            ''',
            '''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Publish_time')
            BEGIN
                CREATE TABLE Publish_time (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    sub_id INT NOT NULL,
                    pub_time NVARCHAR(255) NOT NULL,
                    sended INT NOT NULL DEFAULT 0,
                    FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
                );
            END;
            '''
        ]

        try:
            for query in create_queries:
                await self.execute(query)
                logging.info(f"Executed query: {query[:50]}...")  # Логируем первые 50 символов запроса
        except Exception as exc:
            logging.error("Error creating tables in Azure SQL: %s", exc, exc_info=True)
