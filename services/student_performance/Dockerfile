FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения и .env файла
COPY . .
COPY .env .env

# Создание и настройка прав на медиа-директорию
RUN mkdir -p media && chmod 777 media

# Открываем порт
EXPOSE 8003

# Запуск приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8003"] 