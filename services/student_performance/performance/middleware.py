import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseRedirect
from rest_framework import status
import requests
import logging
from django.contrib.auth import login
from django.urls import reverse
from django.utils.crypto import get_random_string
from .models import Student

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем OPTIONS запросы для CORS
        if request.method == 'OPTIONS':
            return self.get_response(request)

        # Пропускаем запросы к статическим файлам и публичным URL
        if request.path.startswith(('/static/', '/api/public/')):
            return self.get_response(request)
            
        # Пропускаем запросы к API создания профиля
        if request.path == '/api/create-profile/':
            logger.info("API create-profile request - skipping authentication")
            return self.get_response(request)

        if request.path != '/api/token/':
            token = request.COOKIES.get('token')
            if not token:
                logger.info("No token found, redirecting to login")
                return HttpResponseRedirect(settings.LOGIN_URL)
            
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                user_id = decoded.get('user_id')
                if not user_id:
                    logger.warning("No user_id in token")
                    return HttpResponseRedirect(settings.LOGIN_URL)
                
                # Здесь должна быть логика получения пользователя из базы данных
                # или из другого сервиса
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                    
                    # Проверяем, нужно ли обновить статус администратора
                    is_admin = False
                    role = decoded.get('role', '').upper()
                    if role == 'ADMIN' or decoded.get('is_staff') or decoded.get('is_superuser'):
                        is_admin = True
                        
                    if is_admin and (not user.is_staff or not user.is_superuser):
                        logger.info(f"Upgrading user {user.username} to admin status")
                        user.is_staff = True
                        user.is_superuser = True
                        user.save()
                    
                    login(request, user)
                except User.DoesNotExist:
                    logger.error(f"User with id {user_id} not found")
                    
                    # Проверяем, есть ли профиль в нашей базе данных
                    student = Student.objects.filter(user_id=user_id).first()
                    if student:
                        logger.info(f"Found student profile for user_id {user_id}, creating Django user")
                        # Создаем пользователя в Django на основе данных из JWT
                        username = decoded.get('username', f'user_{user_id}')
                        email = decoded.get('email', '')
                        
                        # Проверяем роль пользователя
                        is_admin = False
                        role = decoded.get('role', '').upper()
                        if role == 'ADMIN' or decoded.get('is_staff') or decoded.get('is_superuser'):
                            is_admin = True
                            logger.info(f"Creating user {username} with admin privileges")
                        
                        # Создаем пользователя с временным паролем (он не будет использоваться)
                        user = User.objects.create_user(
                            id=user_id,
                            username=username,
                            email=email,
                            password=get_random_string(length=12)
                        )
                        
                        # Если пользователь админ, устанавливаем соответствующие флаги
                        if is_admin:
                            user.is_staff = True  # Доступ к админке
                            user.is_superuser = True  # Полные права
                        
                        # Добавляем имя и фамилию, если они есть в токене
                        if 'first_name' in decoded:
                            user.first_name = decoded.get('first_name')
                        if 'last_name' in decoded:
                            user.last_name = decoded.get('last_name')
                        
                        user.save()
                        login(request, user)
                        logger.info(f"Created and logged in Django user {username} with id {user_id}")
                    else:
                        return HttpResponseRedirect(settings.LOGIN_URL)
                
            except jwt.InvalidTokenError as e:
                logger.error(f"Invalid token: {str(e)}")
                return HttpResponseRedirect(settings.LOGIN_URL)
            except Exception as e:
                logger.error(f"Error processing token: {str(e)}")
                return HttpResponseRedirect(settings.LOGIN_URL)
        
        response = self.get_response(request)
        return response 