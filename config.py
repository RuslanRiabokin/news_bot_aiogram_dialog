# Config.py
# Конфігураційний файл для проєкту.
# Містить токени для Telegram бота, ключі для API, налаштування бази даних та інші параметри.

import os
import sys

from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name, default=None):
    """ Получить переменную окружения или завершить работу при её отсутствии, если default не указан """
    value = os.environ.get(name, default)
    if value is None:
        print(f"Ошибка: не найдена переменная окружения {name}")
        sys.exit(1)
    return value

# Отримуємо змінні оточення для бота та Webhook
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_BASE_URL = os.getenv("BASE_WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
APP_HOST = os.getenv("WEB_SERVER_HOST")
APP_PORT = int(os.getenv("WEB_SERVER_PORT"))
DB_PATH = os.getenv("DB_PATH")

WEB_SERVER_HOST = get_env_variable("WEB_SERVER_HOST", "127.0.0.1")
WEB_SERVER_PORT = int(get_env_variable("WEB_SERVER_PORT", 8080))
WEBHOOK_PATH = get_env_variable("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = get_env_variable("WEBHOOK_SECRET", "my-secret")
BASE_WEBHOOK_URL = get_env_variable("BASE_WEBHOOK_URL", "https://yourdomain.com")

# News API keys here
BG_KEY_1 = os.getenv("BG_KEY_1")  # Azure Bing News Search Api key 1
BG_KEY_2 = os.getenv("BG_KEY_2")  # Azure Bing News Search Api key 2
BGS_KEY_1 = os.getenv("BGS_KEY_1")  # Azure Bing Search Api key 1
BGS_KEY_2 = os.getenv("BGS_KEY_2")  # Azure Bing Search Api key 1
BG_ENDPOINT = os.getenv("BG_ENDPOINT")  # Azure Bing News Search endpoint
BGS_ENDPOINT = os.getenv("BGS_ENDPOINT")  # Azure Bing Search endpoint
ADMIN_ID = os.environ.get("ADMIN_ID")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройки для Azure SQL
AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
AZURE_SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
AZURE_SQL_USER = os.getenv("AZURE_SQL_USER")
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")
AZURE_SQL_CONNECTION_STRING = f"Driver={{ODBC Driver 17 for SQL Server}};Server={AZURE_SQL_SERVER};Database={AZURE_SQL_DATABASE};UID={AZURE_SQL_USER};PWD={AZURE_SQL_PASSWORD}"

