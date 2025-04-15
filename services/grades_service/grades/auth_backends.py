from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class JWTBackend:
    """Бэкенд для аутентификации пользователя по JWT токену"""
    
    def __init__(self):
        self.jwt_auth = JWTAuthentication()
    
    def authenticate(self, request, jwt_token=None):
        if not jwt_token:
            return None
        
        try:
            validated_token = self.jwt_auth.get_validated_token(jwt_token)
            user_info = {
                'user_id': validated_token.get('user_id', ''),
                'username': validated_token.get('username', ''),
                'email': validated_token.get('email', ''),
                'first_name': validated_token.get('first_name', ''),
                'last_name': validated_token.get('last_name', ''),
                'role': validated_token.get('role', ''),
            }
            return CustomUser(user_info)
        except Exception as e:
            logger.error(f"JWT Backend: {str(e)}")
            return None
    
    def get_user(self, user_id):
        # Этот метод требуется для бэкенда, но не используется в нашей реализации
        return None


class CustomUser(AnonymousUser):
    """Пользовательский класс для хранения информации о пользователе из JWT"""
    
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

    def get_full_name(self):
        """Получение полного имени пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username 