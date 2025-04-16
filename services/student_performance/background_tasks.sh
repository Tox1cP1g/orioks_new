#!/bin/bash

# Активируем виртуальное окружение
source venv1/bin/activate

# Установка задачи синхронизации по расписанию 
python3 sync_teachers.py --schedule

# Запуск процессора фоновых задач
python3 manage.py process_tasks 