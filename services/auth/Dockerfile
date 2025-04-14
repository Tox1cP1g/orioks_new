FROM python:3.11

WORKDIR /app

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Открываем порт
EXPOSE 8002

# Запуск приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"] 