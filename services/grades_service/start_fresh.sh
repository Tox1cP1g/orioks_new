#!/bin/bash

# Убиваем все процессы Python, которые могут быть запущены с manage.py
echo "Killing all Python processes..."
pkill -f "python.*manage.py" || true

# Чистим порт 8005
echo "Cleaning port 8005..."
lsof -ti :8005 | xargs kill -9 2>/dev/null || true

# Создаем директорию для логов
echo "Creating logs directory..."
mkdir -p logs
touch logs/grades.log

# Явно устанавливаем переменную окружения для настроек Django
echo "Setting Django settings module..."
export DJANGO_SETTINGS_MODULE=grades_service.settings

# Запускаем сервер с явным указанием настроек и пути
echo "Starting Django server on port 8005..."
cd /Users/marksmorckov/Downloads/vus/PIUS/orioks_new/services/grades_service
python3 manage.py runserver 8005 