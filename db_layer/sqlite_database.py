import logging
from typing import Optional

import aiosqlite

from db_layer.abstract_database import AbstractDatabase

logging.basicConfig(level=logging.INFO)

class SQLiteDatabase(AbstractDatabase):
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_name)
        await self.connection.execute('PRAGMA foreign_keys=1')
        await self.connection.commit()

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            self.connection = None

    async def execute(self, query: str, params: tuple = ()):  # Загальний метод для виконання SQL-запитів
        if not self.connection:
            raise RuntimeError("Database connection is not established.")
        await self.connection.execute(query, params)
        await self.connection.commit()

    async def fetchone(self, query: str, params: tuple = ()):  # Отримання одного результату
        if not self.connection:
            raise RuntimeError("Database connection is not established.")
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = ()):  # Отримання всіх результатів
        if not self.connection:
            raise RuntimeError("Database connection is not established.")
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchall()

    async def create_tables(self):
        """Створює всі необхідні таблиці в базі даних."""
        queries = [
            '''CREATE TABLE IF NOT EXISTS News (
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
            )''',
            '''CREATE TABLE IF NOT EXISTS Publish_date (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sub_id INTEGER NOT NULL,
                pub_time TEXT NOT NULL,
                FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS Publish_time (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sub_id INTEGER NOT NULL,
                pub_time TEXT NOT NULL,
                sended INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (sub_id) REFERENCES News(id) ON DELETE CASCADE
            )'''
        ]
        for query in queries:
            await self.execute(query)

# Приклад використання
async def main():
    db = SQLiteDatabase("database.db")
    await db.connect()
    await db.create_tables()
    await db.disconnect()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
