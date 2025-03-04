# Используем официальный Python образ на Debian 11 (Bullseye)
FROM python:3.11-bullseye

# Указываем метаданные версии сборки
LABEL version="news_bot v1.0.0"
LABEL description="Docker container for news_bot project version 1.0.0"

# Устанавливаем переменные окружения для корректной кодировки
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=UTF-8

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . .

# Устанавливаем локали
RUN apt-get update && apt-get install -y locales && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    echo "C.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen

# Добавляем репозиторий Microsoft и устанавливаем msodbcsql18
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl -sSL https://packages.microsoft.com/config/debian/11/prod.list -o /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем системные зависимости для Playwright
RUN apt-get update && apt-get install -y \
        curl \
        apt-transport-https \
        ca-certificates \
        gnupg2 \
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libpangocairo-1.0-0 \
        libpango-1.0-0 \
        libgtk-3-0 \
        libx11-xcb1 \
        libxss1 \
        libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузеры для Python Playwright
RUN python -m playwright install --with-deps

# Указываем команду для запуска бота
CMD ["python", "-m", "news_bot"]
