from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.http import HttpResponse, JsonResponse
import logging
from auth_app.models import User, WebAuthnCredential

User = get_user_model()
logger = logging.getLogger(__name__)

def create_test_user(request):
    """
    Создает тестового пользователя и входит в систему.
    Это функция только для тестирования WebAuthn в среде разработки.
    """
    username = 'testuser'
    
    try:
        # Проверяем, существует ли пользователь
        user = User.objects.get(username=username)
        messages.success(request, f'Пользователь {username} уже существует. Выполнен вход в систему.')
    except User.DoesNotExist:
        # Создаем нового пользователя
        user = User.objects.create_user(
            username=username,
            password='testpassword',
            email='test@example.com',
            first_name='Тестовый',
            last_name='Пользователь',
            role='STUDENT'
        )
        messages.success(request, f'Создан новый пользователь {username} и выполнен вход в систему.')
    
    # Входим в систему
    login(request, user)
    
    # Проверяем, есть ли у пользователя ключи безопасности
    has_keys = WebAuthnCredential.objects.filter(user=user).exists()
    
    if has_keys:
        messages.info(request, 'У пользователя уже есть зарегистрированные ключи безопасности.')
    else:
        messages.info(request, 'У пользователя пока нет зарегистрированных ключей безопасности. Пожалуйста, добавьте ключ на странице управления ключами.')
    
    # Перенаправляем на главную страницу вместо страницы управления ключами
    # Временно отключено: return redirect('webauthn_keys_list')
    messages.info(request, 'Страница управления ключами безопасности временно недоступна')
    return redirect('/') 