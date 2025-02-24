# Используем официальный Python образ
FROM python:3.11

# Указываем метаданные версии сборки
LABEL version="news_bot v1.0.0"
LABEL description="Docker container for news_bot project version 1.0.0"

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . .

#Устанавливаем Node.js и npx для выполнения команды playwright
RUN apt-get update && apt-get install -y \
    curl apt-transport-https ca-certificates gnupg2 && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    echo "deb [arch=amd64] https://packages.microsoft.com/ubuntu/20.04/prod focal main" | tee /etc/apt/sources.list.d/mssql-release.list && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y \
        nodejs \
        unixodbc \
        unixodbc-dev \
        msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем playwright с зависимостями
RUN npx playwright install --with-deps

# Указываем команду для запуска бота
CMD ["python", "-m", "news_bot"]
