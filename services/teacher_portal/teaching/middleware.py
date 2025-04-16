import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import status
import requests
from django.shortcuts import redirect
import logging
from django.contrib.auth import login
from .models import Teacher

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Список путей, которые не требуют аутентификации
        self.exempt_paths = [
            '/static/',
            '/admin/',
            '/login/',
            '/api/',
            '/favicon.ico',
            '/media/',
            '/logout/',
            '/raw-json-api/',
            '/public-teacher-subjects/',
            '/public-teacher-subjects.json',
            '/api/public/',
            '/api/v1/public/',
            '/teachers.json'
        ]

    def __call__(self, request):
        # Проверяем, нужно ли пропустить запрос
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)

        # Проверяем наличие токена в cookie
        token = request.COOKIES.get('token')
        if not token:
            logger.info("No token found in cookies")
            return redirect('http://localhost:8002/login/')

        try:
            # Декодируем токен без проверки подписи
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded.get('user_id')
            role = decoded.get('role')

            if not user_id:
                logger.warning("No user_id in token")
                return redirect('http://localhost:8002/login/')

            # Проверяем роль пользователя
            if role != 'TEACHER':
                logger.warning(f"User role {role} is not TEACHER")
                return redirect('http://localhost:8002/login/')

            # Получаем или создаем пользователя
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                # Если пользователь не существует, создаем его
                user = User.objects.create(
                    id=user_id,
                    username=f"teacher_{user_id}",
                    is_active=True
                )
                # Создаем профиль преподавателя
                Teacher.objects.get_or_create(user=user)

            login(request, user)
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return redirect('http://localhost:8002/login/')
        except Exception as e:
            logger.error(f"Error processing token: {str(e)}")
            return redirect('http://localhost:8002/login/')
        
        response = self.get_response(request)
        return response 