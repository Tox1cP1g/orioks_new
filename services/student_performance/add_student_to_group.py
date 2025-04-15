#!/usr/bin/env python
import os
import django
import sys

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_performance.settings')
django.setup()

# Импорт моделей
from performance.models import Student, Group

def add_user_to_group(user_id, group_name):
    try:
        # Получаем группу
        group = Group.objects.get(name=group_name)
        
        # Проверяем, существует ли уже студент с таким user_id
        student, created = Student.objects.get_or_create(
            user_id=user_id,
            defaults={
                'student_number': f'ST{user_id}',
                'faculty': group.faculty
            }
        )
        
        # Устанавливаем группу для студента
        student.group = group
        student.faculty = group.faculty
        student.save()
        
        if created:
            print(f"Создан новый студент с ID {user_id} и добавлен в группу {group_name}")
        else:
            print(f"Студент с ID {user_id} обновлен и добавлен в группу {group_name}")
            
        return True
    except Group.DoesNotExist:
        print(f"Ошибка: Группа {group_name} не найдена")
        return False
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python add_student_to_group.py <user_id> <group_name>")
        print("Пример: python add_student_to_group.py 2 ИУ5-51Б")
        
        # Список доступных групп
        print("\nДоступные группы:")
        for group in Group.objects.all():
            print(f"- {group.name} ({group.faculty}, {group.course} курс)")
        
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    group_name = sys.argv[2]
    
    add_user_to_group(user_id, group_name) 