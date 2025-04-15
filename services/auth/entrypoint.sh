#!/bin/sh

# Ждем доступности базы данных
echo "Waiting for database..."
sleep 5

# Создаем миграции
python manage.py makemigrations

# Применяем миграции
python manage.py migrate

# Создаем суперпользователя, если его нет
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@orioks.ru', 'admin123', role='ADMIN')
"

# Запускаем сервер
exec gunicorn auth_service.wsgi:application --bind 0.0.0.0:8000 