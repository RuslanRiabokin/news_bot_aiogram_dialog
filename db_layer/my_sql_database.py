import logging
import aiomysql
from db_layer.abstract_database import AbstractDatabase

logging.basicConfig(level=logging.INFO)


class MySQLDatabase(AbstractDatabase):
    """Класс для работы с MySQL."""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    async def connect(self):
        """Подключение к MySQL."""
        try:
            self.connection = await aiomysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database
            )
            logging.info("Подключение к MySQL установлено.")
        except Exception as e:
            logging.error(f"Ошибка подключения к MySQL: {e}")

    async def disconnect(self):
        """Отключение от MySQL."""
        if self.connection:
            self.connection.close()
            logging.info("Подключение к MySQL закрыто.")

    async def execute(self, query: str, params: tuple = ()):
        """Выполнение SQL-запроса."""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params)
                await self.connection.commit()
        except Exception as e:
            logging.error(f"Ошибка выполнения SQL-запроса: {e}")

    async def fetchone(self, query: str, params: tuple = ()):
        """Получение одного результата."""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchone()
        except Exception as e:
            logging.error(f"Ошибка fetchone в MySQL: {e}")

    async def fetchall(self, query: str, params: tuple = ()):
        """Получение всех результатов."""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка fetchall в MySQL: {e}")

    async def create_tables(self):
        """Создание таблиц."""
        try:
            await self.execute('''
            CREATE TABLE IF NOT EXISTS News (
                id INT AUTO_INCREMENT PRIMARY KEY,
                topic_name VARCHAR(255) NOT NULL,
                channel_name VARCHAR(255) NOT NULL,
                channel_url VARCHAR(255) NOT NULL,
                last_pub_time VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                news_type VARCHAR(255) NOT NULL,
                publish_frequency VARCHAR(255) NOT NULL,
                language_code VARCHAR(255) NOT NULL,
                add_poll TINYINT NOT NULL,
                is_active TINYINT NOT NULL,
                poll_text TEXT NOT NULL
            )
            ''')
            await self.execute('''
            CREATE TABLE IF NOT EXISTS Publish_date (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sub_id INT NOT NULL,
                pub_time VARCHAR(255) NOT NULL,
                FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
            )
            ''')
            await self.execute('''
            CREATE TABLE IF NOT EXISTS Publish_time (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sub_id INT NOT NULL,
                pub_time VARCHAR(255) NOT NULL,
                sended TINYINT NOT NULL DEFAULT 0,
                FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
            )
            ''')
        except Exception as e:
            logging.error(f"Ошибка создания таблиц в MySQL: {e}")
