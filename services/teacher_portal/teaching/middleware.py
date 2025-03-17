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
            '/logout/'
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
            # Декодируем токен для получения информации о пользователе
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                logger.info(f"Token payload: {payload}")
            except jwt.InvalidTokenError:
                logger.error("Invalid token format")
                return redirect('http://localhost:8002/login/')

            user_id = payload.get('user_id')
            email = payload.get('email', '')
            first_name = payload.get('first_name', '')
            last_name = payload.get('last_name', '')
            is_staff = payload.get('is_staff', False)
            is_superuser = payload.get('is_superuser', False)
            role = payload.get('role', '')

            # Проверяем роль пользователя
            if role not in ['TEACHER', 'ADMIN']:
                logger.info(f"User role {role} not allowed")
                return redirect('http://localhost:8003/')

            # Получаем или создаем пользователя
            try:
                user = User.objects.get(id=user_id)
                # Обновляем данные существующего пользователя
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save(update_fields=['email', 'first_name', 'last_name', 'is_staff', 'is_superuser'])
            except User.DoesNotExist:
                username = f"user_{user_id}"
                user = User.objects.create(
                    id=user_id,
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_superuser=is_superuser
                )

            # Создаем или обновляем профиль преподавателя
            if role == 'TEACHER':
                teacher, created = Teacher.objects.get_or_create(
                    user=user,
                    defaults={
                        'department': payload.get('department', ''),
                        'position': payload.get('position', '')
                    }
                )
                if not created:
                    teacher.department = payload.get('department', '')
                    teacher.position = payload.get('position', '')
                    teacher.save()

            # Аутентифицируем пользователя
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            request.user = user

            logger.info(f"User authenticated: {request.user.is_authenticated}")
            logger.info(f"User full name: {request.user.get_full_name()}")

            response = self.get_response(request)

            # Если это TemplateResponse, добавляем информацию о пользователе в контекст
            if hasattr(response, 'context_data') and response.context_data is not None:
                response.context_data['user'] = user
                full_name = f"{user.first_name} {user.last_name}".strip()
                response.context_data['user_full_name'] = full_name if full_name else user.username
                response.context_data['is_teacher'] = hasattr(user, 'teacher')
                logger.info(f"Context data: {response.context_data}")

            return response

        except Exception as e:
            logger.error(f"Error in middleware: {str(e)}")
            return redirect('http://localhost:8002/login/') 