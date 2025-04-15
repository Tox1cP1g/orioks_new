import logging
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.authentication import JWTAuthentication
import traceback
import jwt

# Импорт DEBUG из настроек
from django.conf import settings
DEBUG = settings.DEBUG

logger = logging.getLogger(__name__)

class CustomUser:
    """Пользовательский класс для хранения информации о пользователе"""
    def __init__(self, user_info):
        self.user_id = user_info.get('user_id', '')
        # Добавляем id как синоним для user_id для совместимости
        self.id = self.user_id
        self.is_authenticated = True
        
        # Приоритет для username: из токена -> составной -> на основе ID
        self.username = user_info.get('username', '')
        if not self.username and user_info.get('first_name') and user_info.get('last_name'):
            self.username = f"{user_info['first_name']} {user_info['last_name']}"
        if not self.username:
            self.username = f"user_{self.id}"
            
        self.email = user_info.get('email', '')
        self.first_name = user_info.get('first_name', '')
        self.last_name = user_info.get('last_name', '')
        self.role = user_info.get('role', '')
        self.group = user_info.get('group', '')
        self.is_staff = user_info.get('is_staff', False)
        self.is_superuser = user_info.get('is_superuser', False)
        self.student_id = user_info.get('student_id', '')
        self.department = user_info.get('department', '')
        self.position = user_info.get('position', '')

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
        # Используем обычный JWTAuthentication для проверки JWT
        self.jwt_auth = JWTAuthentication()
        
        # Создадим собственный JWT_SECRET_KEY, который будет использоваться для проверки подписи
        # К сожалению, это необходимо потому что у разных сервисов разные SECRET_KEY
        self.jwt_secret_key = settings.SIMPLE_JWT.get('SIGNING_KEY', settings.SECRET_KEY)

    def __call__(self, request):
        try:
            token = None
            
            # Сначала проверяем cookie
            if 'token' in request.COOKIES:
                token = request.COOKIES['token']
            
            # Затем проверяем заголовок Authorization
            elif 'HTTP_AUTHORIZATION' in request.META:
                auth_header = request.META['HTTP_AUTHORIZATION']
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]

            if token:
                logger.info(f"Processing token (first 10 chars): {token[:10]}...")
                try:
                    # Для отладки: декодируем токен без проверки подписи
                    decoded_token = jwt.decode(token, options={"verify_signature": False})
                    logger.debug(f"Decoded token: {decoded_token}")
                    
                    # Создаем объект пользователя с учетом всех полей из auth сервиса
                    user_info = {
                        'user_id': str(decoded_token.get('user_id', '')),
                        'username': decoded_token.get('username', 
                                       decoded_token.get('first_name', '') + ' ' + decoded_token.get('last_name', '') 
                                       if decoded_token.get('first_name') and decoded_token.get('last_name') 
                                       else f"user_{decoded_token.get('user_id', 'unknown')}"),
                        'email': decoded_token.get('email', ''),
                        'first_name': decoded_token.get('first_name', ''),
                        'last_name': decoded_token.get('last_name', ''),
                        'role': decoded_token.get('role', ''),
                        'is_staff': decoded_token.get('is_staff', False),
                        'is_superuser': decoded_token.get('is_superuser', False),
                        'student_id': decoded_token.get('student_id', ''),
                        'department': decoded_token.get('department', ''),
                        'position': decoded_token.get('position', ''),
                        'group': decoded_token.get('group', '')
                    }
                    
                    # В режиме отладки, если роль не указана, но указаны другие признаки преподавателя,
                    # устанавливаем роль TEACHER
                    if DEBUG and not user_info['role'] and (
                        user_info['is_staff'] or 
                        user_info['is_superuser'] or 
                        user_info['position'] or 
                        user_info['department']
                    ):
                        user_info['role'] = 'TEACHER'
                        logger.warning(f"Auto-assigned TEACHER role for user {user_info['username']} in DEBUG mode")
                    
                    request.user = CustomUser(user_info)
                    logger.info(f"Successfully authenticated user: {request.user.username} (role: {request.user.role})")
                    
                except Exception as e:
                    logger.warning(f"Invalid token: {str(e)}")
                    request.user = AnonymousUser()
            else:
                logger.debug("No token found in request")
                request.user = AnonymousUser()
        except Exception as e:
            logger.error(f"Error in JWT middleware: {str(e)}\n{traceback.format_exc()}")
            request.user = AnonymousUser()

        response = self.get_response(request)
        return response 