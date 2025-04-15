#!/bin/bash
set -e

# Выполнить миграции
echo "Applying migrations..."
python manage.py migrate

# Запустить сервер
echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8003 