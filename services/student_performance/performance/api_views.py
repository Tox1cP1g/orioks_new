from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
import uuid

from .models import Student

logger = logging.getLogger(__name__)

@csrf_exempt  # Отключаем CSRF для межсервисных вызовов
@require_POST
def create_user_profile(request):
    """API для создания профиля пользователя из сервиса аутентификации"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        username = data.get('username')
        
        logger.info(f"Получен запрос на создание профиля для пользователя {username} (ID: {user_id})")
        
        # Проверяем, есть ли необходимые данные
        if not user_id or not username:
            logger.warning("Не указаны обязательные поля: user_id, username")
            return JsonResponse({
                'status': 'error',
                'message': 'Не указаны обязательные поля: user_id, username'
            }, status=400)
        
        # Проверяем, существует ли уже профиль
        if Student.objects.filter(user_id=user_id).exists():
            logger.info(f"Профиль для пользователя с ID {user_id} уже существует")
            return JsonResponse({
                'status': 'exists',
                'message': f'Профиль для пользователя с ID {user_id} уже существует'
            })
        
        # Генерируем студенческий номер, если не указан
        student_number = data.get('student_number', f"ST{uuid.uuid4().hex[:8].upper()}")
        
        # Создаем профиль
        student = Student.objects.create(
            user_id=user_id,
            student_number=student_number,
            group=data.get('group', 'Не указана'),
            faculty=data.get('faculty', 'Не указан'),
        )
        
        logger.info(f"Создан профиль для пользователя {username} (ID: {user_id})")
        
        return JsonResponse({
            'status': 'success', 
            'student_id': student.id,
            'student_number': student.student_number,
            'message': f'Профиль для пользователя {username} успешно создан'
        })
        
    except json.JSONDecodeError:
        logger.error("Получены некорректные данные JSON")
        return JsonResponse({
            'status': 'error',
            'message': 'Некорректный формат JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Ошибка при создании профиля пользователя: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при создании профиля: {str(e)}'
        }, status=500) 