from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenRefreshView
from api import views

def redirect_to_login(request):
    if request.user.is_authenticated:
        if request.user.role == 'TEACHER':
            return redirect('http://localhost:8004/')
        elif request.user.role == 'ADMIN':
            return redirect('http://localhost:8002/admin/')
        else:
            return redirect('http://localhost:8003/')
    return redirect('http://localhost:8002/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', redirect_to_login, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
] 