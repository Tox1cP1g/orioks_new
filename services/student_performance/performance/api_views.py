from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth import get_user_model
import json
import logging
import uuid
from .models import Student, Group  # Добавляем импорт моделей
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)
User = get_user_model()

@csrf_exempt  # Отключаем CSRF для межсервисных вызовов
@require_POST
def create_user_profile(request):
    """API для создания профиля пользователя из сервиса аутентификации"""
    logger.debug("create_user_profile called")
    
    # Проверяем, есть ли тело запроса
    if not request.body:
        logger.error("Тело запроса пустое")
        return JsonResponse({
            'status': 'error',
            'message': 'Тело запроса пустое'
        }, status=400)
    
    logger.debug(f"Request body: {request.body}")
    
    # Тестовое создание профиля с фиксированными данными
    if request.META.get('HTTP_X_TEST_MODE') == 'true':
        try:
            # Получаем или создаем группу
            default_group, created = Group.objects.get_or_create(
                name='Тестовая группа',
                defaults={
                    'faculty': 'Тестовый факультет',
                    'course': 1
                }
            )
            
            # Создаем или обновляем студента
            test_user_id = 9999
            student, created = Student.objects.update_or_create(
                user_id=test_user_id,
                defaults={
                    'student_number': 'TEST12345',
                    'group': default_group,
                    'faculty': 'Тестовый факультет'
                }
            )
            
            return JsonResponse({
                'status': 'success', 
                'student_id': student.id,
                'student_number': student.student_number,
                'message': f'Тестовый профиль создан или обновлен'
            })
        except Exception as e:
            logger.error(f"Ошибка при создании тестового профиля: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка при создании тестового профиля: {str(e)}'
            }, status=500)
    
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data for profile creation: {data}")
        
        user_id = data.get('user_id')
        username = data.get('username')
        email = data.get('email', '')
        role = data.get('role', 'STUDENT')
        
        logger.info(f"Получен запрос на создание профиля для пользователя {username} (ID: {user_id})")
        
        # Проверяем, есть ли необходимые данные
        if not user_id or not username:
            logger.warning(f"Не указаны обязательные поля: user_id={user_id}, username={username}")
            return JsonResponse({
                'status': 'error',
                'message': 'Не указаны обязательные поля: user_id, username'
            }, status=400)
        
        # Создаем или получаем пользователя в Django
        try:
            user, created = User.objects.get_or_create(
                id=user_id,
                defaults={
                    'username': username,
                    'email': email,
                    'password': get_random_string(length=12)  # Создаем случайный пароль
                }
            )
            if created:
                logger.info(f"Создан новый пользователь Django: {username}")
            else:
                logger.info(f"Найден существующий пользователь Django: {username}")
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя Django: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка при создании пользователя Django: {str(e)}'
            }, status=500)
        
        # Проверяем, существует ли уже профиль
        if Student.objects.filter(user_id=user_id).exists():
            logger.info(f"Профиль для пользователя с ID {user_id} уже существует")
            return JsonResponse({
                'status': 'exists',
                'message': f'Профиль для пользователя с ID {user_id} уже существует'
            })
        
        # Генерируем студенческий номер, если не указан
        student_number = data.get('student_number', f"ST{uuid.uuid4().hex[:8].upper()}")
        
        # Получаем или создаем группу по умолчанию
        default_group_name = data.get('group', 'Не определена')
        default_faculty = data.get('faculty', 'Не определен')
        
        logger.debug(f"Creating/getting group with name={default_group_name}, faculty={default_faculty}")
        
        try:
            group, created = Group.objects.get_or_create(
                name=default_group_name,
                defaults={
                    'faculty': default_faculty,
                    'course': 1
                }
            )
            if created:
                logger.info(f"Group created: {default_group_name} ({default_faculty}, 1 курс)")
            else:
                logger.info(f"Group found: {default_group_name}")
        except Exception as e:
            logger.error(f"Ошибка при создании группы: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка при создании группы: {str(e)}'
            }, status=500)
        
        # Создаем профиль студента
        try:
            student = Student.objects.create(
                user_id=user_id,
                student_number=student_number,
                group=group,
                faculty=default_faculty
            )
            logger.info(f"Создан профиль студента: {student_number}")
            
            return JsonResponse({
                'status': 'success',
                'student_id': student.id,
                'student_number': student_number,
                'message': f'Профиль студента успешно создан'
            })
        except Exception as e:
            logger.error(f"Ошибка при создании профиля студента: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка при создании профиля студента: {str(e)}'
            }, status=500)
            
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON")
        return JsonResponse({
            'status': 'error',
            'message': 'Ошибка декодирования JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Неожиданная ошибка: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_groups(request):
    """API для получения списка всех групп"""
    try:
        groups = Group.objects.all()
        groups_data = [{
            'id': group.id,
            'name': group.name,
            'faculty': group.faculty,
            'course': group.course
        } for group in groups]
        
        return JsonResponse({
            'status': 'success',
            'groups': groups_data
        })
    except Exception as e:
        logger.error(f"Ошибка при получении списка групп: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_student_info(request, user_id):
    """API для получения информации о студенте"""
    try:
        student = Student.objects.filter(user_id=user_id).first()
        if not student:
            return JsonResponse({
                'status': 'error',
                'message': 'Студент не найден'
            }, status=404)
            
        return JsonResponse({
            'status': 'success',
            'student': {
                'id': student.id,
                'user_id': student.user_id,
                'student_number': student.student_number,
                'group': {
                    'id': student.group.id,
                    'name': student.group.name,
                    'faculty': student.group.faculty,
                    'course': student.group.course
                } if student.group else None,
                'faculty': student.faculty
            }
        })
    except Exception as e:
        logger.error(f"Ошибка при получении информации о студенте: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
def update_student_group(request, user_id):
    """API для обновления группы студента"""
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        if not group_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Не указан ID группы'
            }, status=400)
            
        student = Student.objects.filter(user_id=user_id).first()
        if not student:
            return JsonResponse({
                'status': 'error',
                'message': 'Студент не найден'
            }, status=404)
            
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return JsonResponse({
                'status': 'error',
                'message': 'Группа не найдена'
            }, status=404)
            
        student.group = group
        student.faculty = group.faculty
        student.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Студент успешно добавлен в группу {group.name}',
            'group': {
                'id': group.id,
                'name': group.name,
                'faculty': group.faculty,
                'course': group.course
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Некорректный формат JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Ошибка при обновлении группы студента: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 