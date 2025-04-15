#!/usr/bin/env python
import os
import django
import datetime
from django.utils import timezone

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_performance.settings')
django.setup()

# Импорт моделей
from performance.models import Semester, Group, Subject, Schedule

# Функция для создания базовых данных
def create_test_data():
    # Создаем текущий семестр
    current_semester, created = Semester.objects.get_or_create(
        name="Весенний семестр 2025",
        defaults={
            'start_date': datetime.date(2025, 2, 1),
            'end_date': datetime.date(2025, 5, 31),
            'is_current': True
        }
    )
    
    if created:
        print(f"Создан новый семестр: {current_semester}")
    else:
        # Сбрасываем флаг is_current для всех семестров
        Semester.objects.all().update(is_current=False)
        # Устанавливаем текущий семестр
        current_semester.is_current = True
        current_semester.save()
        print(f"Установлен текущий семестр: {current_semester}")
    
    # Создаем группы
    groups_data = [
        {'name': 'ИУ5-51Б', 'faculty': 'Информатика и системы управления', 'course': 3},
        {'name': 'ИУ7-32Б', 'faculty': 'Информатика и системы управления', 'course': 2},
        {'name': 'ИУ8-43Б', 'faculty': 'Информатика и системы управления', 'course': 4},
        {'name': 'РЛ1-21М', 'faculty': 'Радиоэлектроника и лазерная техника', 'course': 1},
        {'name': 'СМ2-61Б', 'faculty': 'Специальное машиностроение', 'course': 3}
    ]
    
    created_groups = []
    for group_data in groups_data:
        group, created = Group.objects.get_or_create(
            name=group_data['name'],
            defaults={
                'faculty': group_data['faculty'],
                'course': group_data['course']
            }
        )
        created_groups.append(group)
        if created:
            print(f"Создана новая группа: {group}")
        else:
            print(f"Группа уже существует: {group}")
    
    # Создаем предметы
    subjects_data = [
        {'name': 'Математическая логика и теория алгоритмов', 'code': 'МТ-101', 'credits': 4},
        {'name': 'Базы данных', 'code': 'ИУ-202', 'credits': 5},
        {'name': 'Операционные системы', 'code': 'ИУ-305', 'credits': 4},
        {'name': 'Компьютерные сети', 'code': 'ИУ-404', 'credits': 3},
        {'name': 'Искусственный интеллект', 'code': 'ИУ-505', 'credits': 5}
    ]
    
    created_subjects = []
    for subject_data in subjects_data:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            code=subject_data['code'],
            defaults={
                'semester': current_semester,
                'credits': subject_data['credits'],
                'description': f"Описание для предмета {subject_data['name']}"
            }
        )
        created_subjects.append(subject)
        if created:
            print(f"Создан новый предмет: {subject}")
        else:
            # Обновляем семестр для существующего предмета
            subject.semester = current_semester
            subject.save()
            print(f"Предмет уже существует, обновлен семестр: {subject}")
    
    # Создаем расписание
    # Очистим расписание для текущего семестра
    Schedule.objects.filter(semester=current_semester).delete()
    print("Старое расписание удалено")
    
    # Помещения
    rooms = ['424л', '518л', '612ю', '301л', '505ю']
    
    # Преподаватели
    teachers = [
        'Иванов И.И.', 'Петров П.П.', 'Сидорова С.С.', 
        'Кузнецов К.К.', 'Морозова М.М.'
    ]
    
    # Генерируем расписание для каждой группы
    schedule_count = 0
    for group in created_groups:
        for day in range(1, 6):  # Понедельник-пятница
            # Выбираем предметы для этого дня (2-3 пары)
            day_subjects = created_subjects[:3]  # Первые 3 предмета
            
            for i, subject in enumerate(day_subjects):
                # Номер пары (1, 2 или 3)
                lesson_number = i + 1
                
                # Создаем запись в расписании
                schedule = Schedule.objects.create(
                    subject=subject,
                    day_of_week=day,
                    lesson_number=lesson_number,
                    room=rooms[i % len(rooms)],
                    teacher=teachers[i % len(teachers)],
                    is_lecture=(i == 0),  # Первая пара - лекция, остальные - практика
                    group=group.name,
                    semester=current_semester
                )
                schedule_count += 1
    
    print(f"Создано {schedule_count} записей в расписании")
    print("Все тестовые данные успешно созданы!")

if __name__ == "__main__":
    create_test_data() 