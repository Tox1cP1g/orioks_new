FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Открываем порт
EXPOSE 8080

# Устанавливаем права на запуск entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Запуск приложения
CMD ["/app/entrypoint.sh"] 