import aiosqlite
import logging
from db_layer.abstract_database import AbstractDatabase

logging.basicConfig(level=logging.INFO)

class SQLiteDatabase(AbstractDatabase):
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_path)
        await self.connection.execute('PRAGMA foreign_keys=1')
        await self.connection.commit()

    async def disconnect(self):
        if self.connection:
            await self.connection.close()

    async def execute(self, query: str, params: tuple = ()):
        try:
            async with self.connection.execute(query, params) as cursor:
                await self.connection.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"SQLite execute error: {e}")

    async def fetchone(self, query: str, params: tuple = ()):
        try:
            async with self.connection.execute(query, params) as cursor:
                return await cursor.fetchone()
        except Exception as e:
            logging.error(f"SQLite fetchone error: {e}")

    async def fetchall(self, query: str, params: tuple = ()):
        try:
            async with self.connection.execute(query, params) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            logging.error(f"SQLite fetchall error: {e}")

    async def create_tables(self):
        await self.execute('''
        CREATE TABLE IF NOT EXISTS News (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            channel_url TEXT NOT NULL,
            last_pub_time TEXT NOT NULL,
            user_id TEXT NOT NULL,
            news_type TEXT NOT NULL,
            publish_frequency TEXT NOT NULL,
            language_code TEXT NOT NULL,
            add_poll TEXT NOT NULL,
            is_active TEXT NOT NULL,
            poll_text TEXT NOT NULL
        )
        ''')
        await self.execute('''
        CREATE TABLE IF NOT EXISTS Publish_date (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_id INTEGER NOT NULL,
            pub_time TEXT NOT NULL,
            FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
        )
        ''')
        await self.execute('''
        CREATE TABLE IF NOT EXISTS Publish_time (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_id INTEGER NOT NULL,
            pub_time TEXT NOT NULL,
            sended INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
        )
        ''')


