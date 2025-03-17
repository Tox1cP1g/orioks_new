#!/bin/bash

# Ждем, пока PostgreSQL будет готов
echo "Waiting for PostgreSQL..."
sleep 10

# Применяем миграции для сервиса авторизации
echo "Applying migrations for auth service..."
cd /app/services/auth
python manage.py migrate

# Применяем миграции для студенческого портала
echo "Applying migrations for student portal..."
cd /app/services/student_performance
python manage.py migrate

# Применяем миграции для учительского портала
echo "Applying migrations for teacher portal..."
cd /app/services/teacher_portal
python manage.py migrate

echo "All migrations have been applied successfully!" 