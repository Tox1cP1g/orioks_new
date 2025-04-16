from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenRefreshView
from api import views
#from api import webauthn_views
from auth_app.views import create_test_user
from django.http import JsonResponse

def redirect_authenticated_user(request):
    if request.user.is_authenticated:
        if request.user.role == 'TEACHER':
            return redirect('http://localhost:8004/')
        elif request.user.role == 'ADMIN':
            return redirect('http://localhost:8002/admin/')
        else:
            return redirect('http://localhost:8003/')
    return redirect('login')

# Временная функция-заглушка вместо webauthn_keys_list
def webauthn_keys_list_placeholder(request):
    from django.contrib import messages
    messages.info(request, 'Управление ключами безопасности временно недоступно')
    return redirect('/')

# Временные заглушки для WebAuthn API
def webauthn_api_placeholder(request):
    return JsonResponse({
        'status': 'error',
        'message': 'Функционал WebAuthn временно отключен для обслуживания'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', redirect_authenticated_user, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API URLs
    path('api/', include('api.urls')),  # Включаем все URL из api.urls
    
    # Временная заглушка для webauthn_keys_list
    path('webauthn/keys/', webauthn_keys_list_placeholder, name='webauthn_keys_list'),
    
    # WebAuthn URLs - временные заглушки
    path('webauthn/register/begin/', webauthn_api_placeholder, name='webauthn_register_begin'),
    path('webauthn/register/complete/', webauthn_api_placeholder, name='webauthn_register_complete'),
    path('webauthn/authenticate/begin/', webauthn_api_placeholder, name='webauthn_authenticate_begin'),
    path('webauthn/authenticate/complete/', webauthn_api_placeholder, name='webauthn_authenticate_complete'),
    path('webauthn/keys/<path:key_id>/delete/', webauthn_api_placeholder, name='webauthn_key_delete'),
    
    # Новые WebAuthn API пути - временные заглушки
    path('webauthn/api/register/begin/', webauthn_api_placeholder, name='webauthn_api_register_begin'),
    path('webauthn/api/register/complete/', webauthn_api_placeholder, name='webauthn_api_register_complete'),
    path('webauthn/api/authenticate/begin/', webauthn_api_placeholder, name='webauthn_api_authenticate_begin'),
    path('webauthn/api/authenticate/complete/', webauthn_api_placeholder, name='webauthn_api_authenticate_complete'),
    path('webauthn/api/users-with-keys/', webauthn_api_placeholder, name='webauthn_api_users_with_keys'),
    
    # Маршрут для создания тестового пользователя (только для разработки)
    path('create-test-user/', create_test_user, name='create_test_user'),
] 