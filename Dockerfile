# Используем официальный Python образ
FROM python:3.11

# Указываем метаданные версии сборки
LABEL version="news_bot v1.0.0"
LABEL description="Docker container for news_bot project version 1.0.0"

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

#Устанавливаем Node.js и npx для выполнения команды playwright
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Устанавливаем playwright с зависимостями
RUN npx playwright install --with-deps

# Указываем команду для запуска бота
CMD ["python", "-m", "news_bot"]
