import logging
import requests
import json
from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

class TeacherPortalClient:
    """Клиент для взаимодействия с сервисом преподавателей (порт 8004)"""
    
    BASE_URL = "http://localhost:8004/api"
    
    @classmethod
    def get_teachers(cls, token=None):
        """Получает список преподавателей из базы данных или API"""
        try:
            # Сначала пробуем получить данные напрямую из базы данных
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.id, 
                        u.first_name, 
                        u.last_name, 
                        u.email, 
                        p.faculty as department, 
                        'Преподаватель' as position
                    FROM 
                        performance_userprofile p
                    JOIN 
                        auth_user u ON p.user_id = u.id
                    WHERE 
                        p.role = 'TEACHER'
                """)
                columns = [col[0] for col in cursor.description]
                teachers = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                if teachers:
                    logger.info(f"Получено {len(teachers)} преподавателей из базы данных")
                    return teachers
                else:
                    logger.warning("Не найдено преподавателей в базе данных, пробуем получить через API")
            
            # Если не удалось получить данные из базы, пробуем через API
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(f"{cls.BASE_URL}/teachers/", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Не удалось получить список преподавателей через API. Статус: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении списка преподавателей: {str(e)}")
            return []
    
    @classmethod
    def get_teacher_by_id(cls, teacher_id, token=None):
        """Получает информацию о преподавателе по ID из базы данных или API"""
        try:
            # Сначала пробуем получить данные напрямую из базы данных
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.id, 
                        u.first_name, 
                        u.last_name, 
                        u.email, 
                        p.faculty as department, 
                        'Преподаватель' as position
                    FROM 
                        performance_userprofile p
                    JOIN 
                        auth_user u ON p.user_id = u.id
                    WHERE 
                        p.id = %s AND p.role = 'TEACHER'
                """, [teacher_id])
                columns = [col[0] for col in cursor.description]
                teachers = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                if teachers:
                    logger.info(f"Получен преподаватель с ID {teacher_id} из базы данных")
                    return teachers[0]
                else:
                    logger.warning(f"Не найден преподаватель с ID {teacher_id} в базе данных, пробуем получить через API")
            
            # Если не удалось получить данные из базы, пробуем через API
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(f"{cls.BASE_URL}/teachers/{teacher_id}/", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Не удалось получить преподавателя с ID {teacher_id} через API. Статус: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении преподавателя: {str(e)}")
            return None
    
    @classmethod
    def get_teacher_subjects(cls, teacher_id, token=None):
        """Получает список предметов преподавателя из базы данных или API"""
        try:
            # Сначала пробуем получить данные напрямую из базы данных
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        s.id, 
                        s.name, 
                        s.description
                    FROM 
                        performance_subject s
                    JOIN 
                        performance_course c ON s.id = c.subject_id
                    JOIN 
                        performance_userprofile p ON c.teacher_id = p.id
                    WHERE 
                        p.id = %s AND p.role = 'TEACHER'
                """, [teacher_id])
                columns = [col[0] for col in cursor.description]
                subjects = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                if subjects:
                    logger.info(f"Получено {len(subjects)} предметов преподавателя с ID {teacher_id} из базы данных")
                    return subjects
                else:
                    logger.warning(f"Не найдены предметы преподавателя с ID {teacher_id} в базе данных, пробуем получить через API")
            
            # Если не удалось получить данные из базы, пробуем через API
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(f"{cls.BASE_URL}/teachers/{teacher_id}/subjects/", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Не удалось получить предметы преподавателя {teacher_id} через API. Статус: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении предметов преподавателя: {str(e)}")
            return []


class StudentPortalClient:
    """Клиент для взаимодействия с сервисом студентов (порт 8003)"""
    
    BASE_URL = "http://localhost:8003/api"
    
    @classmethod
    def get_students(cls, token=None):
        """Получает список студентов из базы данных или API"""
        try:
            # Сначала пробуем получить данные напрямую из базы данных
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        s.id, 
                        u.first_name, 
                        u.last_name, 
                        u.email, 
                        g.name as group_name,
                        g.id as group_id
                    FROM 
                        performance_student s
                    JOIN 
                        auth_user u ON s.user_id = u.id
                    LEFT JOIN 
                        performance_group g ON s.group_id = g.id
                """)
                columns = [col[0] for col in cursor.description]
                students = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Переименуем поля для совместимости
                for student in students:
                    if 'group_name' in student:
                        student['group'] = student['group_name']
                        del student['group_name']
                
                if students:
                    logger.info(f"Получено {len(students)} студентов из базы данных")
                    return students
                else:
                    logger.warning("Не найдено студентов в базе данных, пробуем получить через API")
            
            # Если не удалось получить данные из базы, пробуем через API
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(f"{cls.BASE_URL}/students/", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Не удалось получить список студентов через API. Статус: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении списка студентов: {str(e)}")
            return []
    
    @classmethod
    def get_student_by_id(cls, student_id, token=None):
        """Получает информацию о студенте по ID из базы данных или API"""
        try:
            # Сначала пробуем получить данные напрямую из базы данных
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        s.id, 
                        u.first_name, 
                        u.last_name, 
                        u.email, 
                        g.name as group_name,
                        g.id as group_id
                    FROM 
                        performance_student s
                    JOIN 
                        auth_user u ON s.user_id = u.id
                    LEFT JOIN 
                        performance_group g ON s.group_id = g.id
                    WHERE 
                        s.id = %s
                """, [student_id])
                columns = [col[0] for col in cursor.description]
                students = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Переименуем поля для совместимости
                for student in students:
                    if 'group_name' in student:
                        student['group'] = student['group_name']
                        del student['group_name']
                
                if students:
                    logger.info(f"Получен студент с ID {student_id} из базы данных")
                    return students[0]
                else:
                    logger.warning(f"Не найден студент с ID {student_id} в базе данных, пробуем получить через API")
            
            # Если не удалось получить данные из базы, пробуем через API
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(f"{cls.BASE_URL}/students/{student_id}/", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Не удалось получить студента с ID {student_id} через API. Статус: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении студента: {str(e)}")
            return None
    
    @classmethod
    def get_groups(cls, token=None):
        """Получает список групп студентов из базы данных или API"""
        try:
            # Сначала пробуем получить данные напрямую из базы данных
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        g.id, 
                        g.name, 
                        g.faculty as department
                    FROM 
                        performance_group g
                """)
                columns = [col[0] for col in cursor.description]
                groups = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                if groups:
                    logger.info(f"Получено {len(groups)} групп из базы данных")
                    return groups
                else:
                    logger.warning("Не найдено групп в базе данных, пробуем получить через API")
            
            # Если не удалось получить данные из базы, пробуем через API
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(f"{cls.BASE_URL}/groups/", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Не удалось получить список групп через API. Статус: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении списка групп: {str(e)}")
            return []
    
    @classmethod
    def get_group_students(cls, group_id, token=None):
        """Получает список студентов группы из базы данных или API"""
        try:
            # Сначала пробуем получить данные напрямую из базы данных
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        s.id, 
                        u.first_name, 
                        u.last_name, 
                        u.email, 
                        g.name as group_name,
                        g.id as group_id
                    FROM 
                        performance_student s
                    JOIN 
                        auth_user u ON s.user_id = u.id
                    JOIN 
                        performance_group g ON s.group_id = g.id
                    WHERE 
                        g.id = %s
                """, [group_id])
                columns = [col[0] for col in cursor.description]
                students = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Переименуем поля для совместимости
                for student in students:
                    if 'group_name' in student:
                        student['group'] = student['group_name']
                        del student['group_name']
                
                if students:
                    logger.info(f"Получено {len(students)} студентов группы с ID {group_id} из базы данных")
                    return students
                else:
                    logger.warning(f"Не найдены студенты группы с ID {group_id} в базе данных, пробуем получить через API")
            
            # Если не удалось получить данные из базы, пробуем через API
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(f"{cls.BASE_URL}/groups/{group_id}/students/", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Не удалось получить студентов группы {group_id} через API. Статус: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении студентов группы: {str(e)}")
            return []


# Утилитарные функции для синхронизации данных
def sync_teachers_from_portal(token=None):
    """Синхронизирует преподавателей из портала преподавателей"""
    from .models import Teacher
    
    try:
        teachers_data = TeacherPortalClient.get_teachers(token)
        
        if not teachers_data:
            logger.warning("Не получены данные о преподавателях для синхронизации")
            return 0
        
        count = 0
        for teacher_data in teachers_data:
            teacher, created = Teacher.objects.update_or_create(
                user_id=teacher_data.get('id'),
                defaults={
                    'first_name': teacher_data.get('first_name', ''),
                    'last_name': teacher_data.get('last_name', ''),
                    'email': teacher_data.get('email', ''),
                    'department': teacher_data.get('department', ''),
                    'position': teacher_data.get('position', '')
                }
            )
            if created:
                count += 1
                logger.info(f"Создан преподаватель: {teacher.get_full_name()}")
            else:
                logger.info(f"Обновлен преподаватель: {teacher.get_full_name()}")
        
        return count
    except Exception as e:
        logger.error(f"Ошибка при синхронизации преподавателей: {str(e)}")
        return 0


def sync_students_and_groups_from_portal(token=None):
    """Синхронизирует студентов и группы из портала студентов"""
    from .models import Student, Group
    
    try:
        # Сначала синхронизируем группы
        groups_data = StudentPortalClient.get_groups(token)
        
        if not groups_data:
            logger.warning("Не получены данные о группах для синхронизации")
            return 0, 0
        
        groups_count = 0
        for group_data in groups_data:
            group, created = Group.objects.update_or_create(
                name=group_data.get('name'),
                defaults={
                    'department': group_data.get('department', '')
                }
            )
            if created:
                groups_count += 1
                logger.info(f"Создана группа: {group.name}")
            else:
                logger.info(f"Обновлена группа: {group.name}")
        
        # Затем синхронизируем студентов
        students_data = StudentPortalClient.get_students(token)
        
        if not students_data:
            logger.warning("Не получены данные о студентах для синхронизации")
            return groups_count, 0
        
        students_count = 0
        for student_data in students_data:
            # Найдем группу по имени
            group_name = student_data.get('group')
            group = None
            if group_name:
                try:
                    group = Group.objects.get(name=group_name)
                except Group.DoesNotExist:
                    logger.warning(f"Группа {group_name} не найдена. Создаем группу.")
                    group = Group.objects.create(name=group_name)
            
            student, created = Student.objects.update_or_create(
                user_id=student_data.get('id'),
                defaults={
                    'first_name': student_data.get('first_name', ''),
                    'last_name': student_data.get('last_name', ''),
                    'email': student_data.get('email', ''),
                    'group': group
                }
            )
            if created:
                students_count += 1
                logger.info(f"Создан студент: {student.get_full_name()}")
            else:
                logger.info(f"Обновлен студент: {student.get_full_name()}")
        
        return groups_count, students_count
    except Exception as e:
        logger.error(f"Ошибка при синхронизации студентов и групп: {str(e)}")
        return 0, 0


# Мок-функции для тестирования в отладочном режиме
if settings.DEBUG:
    def mock_teacher_data():
        """Создает тестовые данные для преподавателей"""
        return [
            {
                'id': 1,
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'email': 'ivanov@example.com',
                'department': 'Кафедра информатики',
                'position': 'Доцент'
            },
            {
                'id': 2,
                'first_name': 'Петр',
                'last_name': 'Петров',
                'email': 'petrov@example.com',
                'department': 'Кафедра математики',
                'position': 'Профессор'
            }
        ]
    
    def mock_group_data():
        """Создает тестовые данные для групп"""
        return [
            {
                'id': 1,
                'name': 'ПИН-34',
                'department': 'Программная инженерия'
            },
            {
                'id': 2,
                'name': 'ИВТ-25',
                'department': 'Информатика и вычислительная техника'
            }
        ]
    
    def mock_student_data(group_id=None):
        """Создает тестовые данные для студентов"""
        students = [
            {
                'id': 1,
                'first_name': 'Алексей',
                'last_name': 'Алексеев',
                'email': 'alekseev@example.com',
                'group_id': 1
            },
            {
                'id': 2,
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'email': 'sidorova@example.com',
                'group_id': 1
            },
            {
                'id': 3,
                'first_name': 'Сергей',
                'last_name': 'Смирнов',
                'email': 'smirnov@example.com',
                'group_id': 2
            }
        ]
        
        if group_id:
            return [s for s in students if s['group_id'] == group_id]
        return students
    
    # Переопределяем методы клиентов для использования мок-данных
    original_teacher_get_teachers = TeacherPortalClient.get_teachers
    original_student_get_groups = StudentPortalClient.get_groups
    original_student_get_students = StudentPortalClient.get_students
    original_student_get_group_students = StudentPortalClient.get_group_students
    
    def debug_get_teachers(self):
        """Мок-версия получения списка преподавателей"""
        try:
            return original_teacher_get_teachers(self)
        except:
            logger.warning("Using mock teacher data in DEBUG mode")
            return mock_teacher_data()
    
    def debug_get_groups(self):
        """Мок-версия получения списка групп"""
        try:
            return original_student_get_groups(self)
        except:
            logger.warning("Using mock group data in DEBUG mode")
            return mock_group_data()
    
    def debug_get_students(self):
        """Мок-версия получения списка студентов"""
        try:
            return original_student_get_students(self)
        except:
            logger.warning("Using mock student data in DEBUG mode")
            return mock_student_data()
    
    def debug_get_group_students(self, group_id):
        """Мок-версия получения списка студентов группы"""
        try:
            return original_student_get_group_students(self, group_id)
        except:
            logger.warning(f"Using mock student data for group {group_id} in DEBUG mode")
            return mock_student_data(group_id)
    
    # Заменяем методы в DEBUG режиме
    TeacherPortalClient.get_teachers = debug_get_teachers
    StudentPortalClient.get_groups = debug_get_groups
    StudentPortalClient.get_students = debug_get_students
    StudentPortalClient.get_group_students = debug_get_group_students 