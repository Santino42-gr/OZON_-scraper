# Bot Dockerfile для OZON Telegram Bot
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY . .

# Создаем директорию для логов
RUN mkdir -p logs

# Запускаем бота
CMD ["python", "main.py"]
