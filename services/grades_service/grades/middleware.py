import logging
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
import traceback
import requests
from django.http import HttpResponseRedirect
from urllib.parse import urljoin

# Импорт DEBUG из настроек
from django.conf import settings
DEBUG = settings.DEBUG

logger = logging.getLogger(__name__)

class CustomUser:
    """Пользовательский класс для хранения информации о пользователе"""
    def __init__(self, user_info):
        self.user_id = user_info.get('id')  # Изменено с 'user_id' на 'id' для соответствия с auth сервисом
        self.id = self.user_id
        self.is_authenticated = True
        
        self.username = user_info.get('username', '')
        self.email = user_info.get('email', '')
        self.first_name = user_info.get('first_name', '')
        self.last_name = user_info.get('last_name', '')
        
        # Дополнительные поля
        self.role = user_info.get('role', '')
        self.is_staff = user_info.get('is_staff', False)
        self.is_superuser = user_info.get('is_superuser', False)

    def get_full_name(self):
        """Получение полного имени пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __str__(self):
        return self.get_full_name()

class JWTAuthMiddleware:
    """Middleware для аутентификации пользователя по JWT токену"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URL для auth сервиса
        self.auth_service_url = "http://localhost:8002"  # Базовый URL
        self.user_info_endpoint = "/api/user/info/"  # Endpoint для получения информации о пользователе
        self.login_url = "http://localhost:8002/login/"  # URL для логина
        logger.info(f"Auth service URL configured as: {self.auth_service_url}")

    def get_user_info_from_auth_service(self, token):
        """Получает информацию о пользователе из auth сервиса"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            url = urljoin(self.auth_service_url, self.user_info_endpoint)
            logger.debug(f"Making request to auth service: {url}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Successfully retrieved user info: {user_data.get('username')}")
                return user_data
            else:
                logger.error(f"Failed to get user info from auth service. Status: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting user info from auth service: {str(e)}")
            logger.debug(traceback.format_exc())
            return None

    def __call__(self, request):
        try:
            # Пропускаем проверку для определенных путей
            if any(request.path.startswith(prefix) for prefix in ['/static/', '/admin/', '/login/', '/api/token/']):
                return self.get_response(request)

            token = None
            
            # Проверяем cookie
            if 'token' in request.COOKIES:
                token = request.COOKIES['token']
            
            # Проверяем заголовок Authorization
            elif 'HTTP_AUTHORIZATION' in request.META:
                auth_header = request.META['HTTP_AUTHORIZATION']
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]

            if token:
                logger.info(f"Processing token (first 10 chars): {token[:10]}...")
                
                # Получаем информацию о пользователе из auth сервиса
                user_info = self.get_user_info_from_auth_service(token)
                
                if user_info:
                    request.user = CustomUser(user_info)
                    logger.info(f"Successfully authenticated user: {request.user.username}")
                else:
                    logger.warning("Failed to get user info from auth service")
                    request.user = AnonymousUser()
                    if not request.path.startswith('/api/'):  # Не делаем редирект для API endpoints
                        return HttpResponseRedirect(self.login_url)
            else:
                logger.debug("No token found in request")
                request.user = AnonymousUser()
                if not request.path.startswith('/api/'):  # Не делаем редирект для API endpoints
                    return HttpResponseRedirect(self.login_url)

        except Exception as e:
            logger.error(f"Error in JWT middleware: {str(e)}")
            logger.debug(traceback.format_exc())
            request.user = AnonymousUser()
            if not request.path.startswith('/api/'):  # Не делаем редирект для API endpoints
                return HttpResponseRedirect(self.login_url)

        response = self.get_response(request)
        return response 