import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from db_layer.database import AsyncDatabase
from db_layer.db_factory import get_data_serice
from news_processing.news_pre_publisher import time_check


class NewsScheduler:
    def __init__(self):
        self.bot = None
        self.is_running = False
        self.current_task = None

    async def get_next_publication_time(self):
        async with get_data_serice() as db:
            times_list = await db.get_last_times_list()
            if not times_list:
                return None

            earliest_time = min(
                datetime.strptime(time['last_pub_time'], "%Y-%m-%d %H:%M:%S")
                for time in times_list
            )

            now = datetime.now()
            if earliest_time > now:
                return earliest_time
            elif earliest_time + timedelta(hours=1) > now:
                return earliest_time + timedelta(hours=1)
            else:
                return now

    async def schedule_next_publication(self):
        if not self.is_running:
            return

        next_time = await self.get_next_publication_time()
        if next_time is None:
            print("No publications scheduled.")
            return

        now = datetime.now()
        delay = (next_time - now).total_seconds()

        print(f"Next publication scheduled for: {next_time}")
        await asyncio.sleep(delay)
        await time_check(self.bot)

        # Schedule the next publication
        self.current_task = asyncio.create_task(self.schedule_next_publication())

    async def start(self, bot: Bot):
        if self.is_running:
            return

        self.bot = bot
        self.is_running = True
        self.current_task = asyncio.create_task(self.schedule_next_publication())

    async def stop(self):
        self.is_running = False
        if self.current_task:
            self.current_task.cancel()


    async def trigger_immediate_check(self):
        if self.current_task:
            self.current_task.cancel()
        await time_check(self.bot)
        self.current_task = asyncio.create_task(self.schedule_next_publication())


# Створюємо глобальний об'єкт планувальника
scheduler = NewsScheduler()

# В main_async() замініть виклик scheduled_news_publishing на:
# await scheduler.start(bot)

# Для зупинки планувальника (наприклад, при завершенні роботи бота):
# await scheduler.stop()

# Для ручного запуску перевірки з будь-якого модуля:
# await scheduler.trigger_immediate_check()