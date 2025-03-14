# News Bot - Telegram News Automation

## Мета проєкту

Чат-бот розроблено для автоматизації отримання та публікації новин в Telegram-канали за заданими темами та налаштуваннями. Бот дозволяє користувачам легко задавати теми, отримувати оброблені новини, та публікувати їх за допомогою API. Забезпечується переклад новин, скорочення текстів та додавання посилань на оригінальні джерела.

---

## Project Purpose

The News Bot is developed to automate the process of retrieving and publishing news in Telegram channels according to user-defined topics and settings. It allows users to conveniently specify topics, process news, and publish them via API. The bot ensures translation, text summarization, and adds original source links.

---

## Основний функціонал / Key Features

### 1. Запит інформації / Information Input
- **Запит теми новин:** Користувач обирає тему новин.
- **Канал Telegram:** Користувач вказує канал для публікації.
- **Права адміністратора:** Якщо права не надані, бот запитує їх.

- **News Topics Input:** User specifies topics of interest.
- **Telegram Channel Selection:** User specifies the channel for news publication.
- **Admin Rights Request:** If admin rights are missing, the bot requests them.

### 2. Отримання новин / News Retrieval
- **Збір даних за API:** Бот отримує новини за API (News API).
- **Переклад новин:** Новини не українською мовою автоматично перекладаються.
- **API Data Collection:** The bot fetches news via API (e.g., News API).
- **Translation:** Automatically translates news if not in the user’s preferred language.

### 3. Обробка новин / News Processing
- **Переклад та скорочення:** Переклад новин на вибрану мову, скорочення для зручності читання.
- **Translation & Summarization:** Translates and shortens the news for readability.

### 4. Публікація / Publishing
- **Публікація за розкладом:** Публікує щодогодини або за вибором користувача.
- **Scheduled Publishing:** Default hourly schedule, adjustable by user.

---

## Технічні особливості / Technical Details

### 1. Архітектура / Architecture
- **news_bot.py:** Головний файл бота.
- **config.py:** Конфігурація API та токени.
- **database.py:** Зберігає дані про теми та канали.

### 2. Бібліотеки / Libraries
- **aiogram-dialog:** Підтримка діалогів.
- **aiogram-dialog:** Dialog management for efficient user interaction.

---

## Deployment
- **Dockerized:** Supports easy deployment via Docker.
- **Environment Variables:** Sensitive data (tokens, keys) stored securely.

---

## Contact / Контакти
- Email: rriabokin@gmail.com
- Telegram: [@news_bot](https://t.me/news_bot)
