import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot_router_aiogram_dialog import register_routes
from config import BOT_TOKEN, BASE_WEBHOOK_URL, WEB_SERVER_HOST, WEB_SERVER_PORT, WEBHOOK_PATH, WEBHOOK_SECRET
from db_layer.db_factory import get_data_serice
from news_processing.news_pre_publisher import time_check


async def set_bot_commands(bot: Bot):
    """Встановлює команди робота для меню."""
    commands = [
        BotCommand(command="/instruction", description="Ознайомитись з інструкцією"),
        BotCommand(command="/start", description="Початок праці"),
        BotCommand(command="/menu", description="Меню Підписок"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(app: web.Application):
    """Функція для запуску Webhook"""
    webhook_info = await app["bot"].get_webhook_info()
    logging.info(f"WEBHOOK_INFO\n{webhook_info}")
    await app["bot"].delete_webhook(drop_pending_updates=True)
    webhook_info = await app["bot"].get_webhook_info()
    logging.info(f"WEBHOOK_INFO\n{webhook_info}")
    await app["bot"].set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET,
                                 allowed_updates=["message", "callback_query", "inline_query"])
    webhook_info = await app["bot"].get_webhook_info()
    logging.info(f"WEBHOOK_INFO\n{webhook_info}")

    # Установка команд для бота
    await set_bot_commands(app["bot"])

    print("Webhook started")


async def on_shutdown(app: web.Application):
    """Функція для зупинки Webhook"""
    await app["bot"].delete_webhook()


stop_event = threading.Event()


async def scheduled_news_publishing():
    """
    Функція для циклічної перевірки та публікації новин,
    та оновлення статусу 'sended', якщо настав новий день.
    """
    try:
        async with get_data_serice() as db:
            await db.create_db()
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        last_checked_day = datetime.now().date()
        while not stop_event.is_set():
            current_day = datetime.now().date()

            if current_day != last_checked_day:
                async with get_data_serice() as db:
                    await db.set_all_sended_status_false()

                last_checked_day = current_day

            await time_check(bot)
            stop_event.wait(60)
    except Exception as e:
        logging.error(f"News processing error occurred: {e}")
    finally:
        logging.info("Finishing news processing...")


def start_scheduled_news_publishing():
    """Запуск функції публікації новин в окремому потоці."""
    asyncio.run(scheduled_news_publishing())

async def health_check(request):
    """
    Responds with HTTP 200 to indicate the app is healthy.
    """
    return web.Response(status=200, text="Healthy")

def main_bot():
    try:
        logging.info("Starting the bot...")
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()
        register_routes(dp)

        app = web.Application()
        app["bot"] = bot
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)
        app.router.add_get("/health", health_check)

        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        logging.info(f"Server started at http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.info("Shutting down...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with ThreadPoolExecutor(max_workers=1) as executor:
        # Запускаємо scheduled_news_publishing в окремому потоці
        executor.submit(start_scheduled_news_publishing)
        main_bot()
        stop_event.set()
