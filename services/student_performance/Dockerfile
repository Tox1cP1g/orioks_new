FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей системы для MySQL
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Порт для внешних подключений
EXPOSE 8003

# Запуск сервера при старте контейнера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8003"] 