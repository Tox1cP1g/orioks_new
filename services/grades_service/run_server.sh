#!/bin/bash

# Останавливаем все процессы Django на порту 8005
echo "Stopping any existing Django processes on port 8005..."
pkill -f "python3 manage.py runserver 8005" || true
pkill -f "python manage.py runserver 8005" || true

# Создаем директорию для логов, если она не существует
echo "Creating logs directory if it doesn't exist..."
mkdir -p logs
touch logs/grades.log

# Проверяем версию Python
echo "Python version:"
python3 -c "import sys; print(sys.version)"

# Устанавливаем переменную окружения для настроек Django
export DJANGO_SETTINGS_MODULE=grades_service.settings

# Запускаем сервер
echo "Starting Django server on port 8005..."
cd /Users/marksmorckov/Downloads/vus/PIUS/orioks_new/services/grades_service
python3 manage.py runserver 8005 