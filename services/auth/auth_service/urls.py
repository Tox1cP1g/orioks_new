from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenRefreshView
from api import views
from api import webauthn_views
from auth_app.views import create_test_user

def redirect_authenticated_user(request):
    if request.user.is_authenticated:
        if request.user.role == 'TEACHER':
            return redirect('http://localhost:8004/')
        elif request.user.role == 'ADMIN':
            return redirect('http://localhost:8002/admin/')
        else:
            return redirect('http://localhost:8003/')
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', redirect_authenticated_user, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # WebAuthn URLs
    path('webauthn/register/begin/', webauthn_views.webauthn_register_begin, name='webauthn_register_begin'),
    path('webauthn/register/complete/', webauthn_views.webauthn_register_complete, name='webauthn_register_complete'),
    path('webauthn/authenticate/begin/', webauthn_views.webauthn_authenticate_begin, name='webauthn_authenticate_begin'),
    path('webauthn/authenticate/complete/', webauthn_views.webauthn_authenticate_complete, name='webauthn_authenticate_complete'),
    path('webauthn/keys/', webauthn_views.webauthn_keys_list, name='webauthn_keys_list'),
    path('webauthn/keys/<uuid:key_id>/delete/', webauthn_views.webauthn_key_delete, name='webauthn_key_delete'),
    
    # Новые WebAuthn API пути для совместимости с новым JavaScript кодом
    path('webauthn/api/register/begin/', webauthn_views.webauthn_register_begin, name='webauthn_api_register_begin'),
    path('webauthn/api/register/complete/', webauthn_views.webauthn_register_complete, name='webauthn_api_register_complete'),
    path('webauthn/api/authenticate/begin/', webauthn_views.webauthn_authenticate_begin, name='webauthn_api_authenticate_begin'),
    path('webauthn/api/authenticate/complete/', webauthn_views.webauthn_authenticate_complete, name='webauthn_api_authenticate_complete'),
    path('webauthn/api/users-with-keys/', webauthn_views.webauthn_users_with_keys, name='webauthn_api_users_with_keys'),
    
    # Маршрут для создания тестового пользователя (только для разработки)
    path('create-test-user/', create_test_user, name='create_test_user'),
] 