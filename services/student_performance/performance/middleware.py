import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseRedirect
from rest_framework import status
import requests
import logging
from django.contrib.auth import login
from django.urls import reverse

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
                    login(request, user)
                except User.DoesNotExist:
                    logger.error(f"User with id {user_id} not found")
                    return HttpResponseRedirect(settings.LOGIN_URL)
                
            except jwt.InvalidTokenError as e:
                logger.error(f"Invalid token: {str(e)}")
                return HttpResponseRedirect(settings.LOGIN_URL)
            except Exception as e:
                logger.error(f"Error processing token: {str(e)}")
                return HttpResponseRedirect(settings.LOGIN_URL)
        
        response = self.get_response(request)
        return response 