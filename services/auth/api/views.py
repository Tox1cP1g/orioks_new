from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from rest_framework_simplejwt.views import TokenVerifyView
import logging

logger = logging.getLogger(__name__)

# Create your views here.

@csrf_protect
def login_view(request):
    logger.info("Login view called")
    logger.info(f"Method: {request.method}")
    logger.info(f"POST data: {request.POST}")
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            logger.info(f"Attempting to authenticate user: {username}")
            
            user = authenticate(username=username, password=password)
            logger.info(f"Authentication result: {user}")
            
            if user is not None:
                # Выполняем вход пользователя
                login(request, user)
                
                # Генерируем JWT токен
                refresh = RefreshToken.for_user(user)
                refresh['first_name'] = user.first_name
                refresh['last_name'] = user.last_name
                refresh['email'] = user.email
                refresh['is_staff'] = user.is_staff
                refresh['is_superuser'] = user.is_superuser
                refresh['role'] = user.role
                
                # Определяем URL для перенаправления
                next_url = request.GET.get('next')
                if next_url:
                    redirect_url = next_url
                else:
                    if user.role == 'TEACHER':
                        redirect_url = 'http://localhost:8004/'
                    elif user.role == 'ADMIN':
                        redirect_url = 'http://localhost:8002/admin/'
                    else:
                        redirect_url = 'http://localhost:8003/'
                
                logger.info(f"Redirecting to: {redirect_url}")
                
                response = redirect(redirect_url)
                response.set_cookie(
                    'token',
                    str(refresh.access_token),
                    max_age=3600,
                    httponly=True,
                    samesite='Lax'
                )
                return response
            else:
                logger.warning("Authentication failed")
                messages.error(request, 'Неверное имя пользователя или пароль')
                return render(request, 'auth/login.html', {
                    'error': 'Неверное имя пользователя или пароль'
                })
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            messages.error(request, 'Произошла ошибка при входе в систему')
            return render(request, 'auth/login.html', {
                'error': 'Произошла ошибка при входе в систему'
            })
    
    logger.info("Rendering login template")
    return render(request, 'auth/login.html')

@csrf_protect
def student_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None and user.role == 'STUDENT':
            refresh = RefreshToken.for_user(user)
            refresh['first_name'] = user.first_name
            refresh['last_name'] = user.last_name
            refresh['email'] = user.email
            refresh['role'] = user.role
            
            response = redirect('http://localhost:8003/')
            response.set_cookie(
                'token',
                str(refresh.access_token),
                max_age=3600,
                httponly=True,
                samesite='Lax'
            )
            return response
        else:
            return render(request, 'auth/student_login.html', {
                'error': 'Неверное имя пользователя или пароль'
            })
    
    return render(request, 'auth/student_login.html')

@csrf_protect
def staff_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None and user.role == 'TEACHER':
            refresh = RefreshToken.for_user(user)
            refresh['first_name'] = user.first_name
            refresh['last_name'] = user.last_name
            refresh['email'] = user.email
            refresh['role'] = user.role
            
            response = redirect('http://localhost:8004/')
            response.set_cookie(
                'token',
                str(refresh.access_token),
                max_age=3600,
                httponly=True,
                samesite='Lax'
            )
            return response
        else:
            return render(request, 'auth/staff_login.html', {
                'error': 'Неверное имя пользователя или пароль'
            })
    
    return render(request, 'auth/staff_login.html')

@csrf_protect
def token_obtain_pair(request):
    if request.method == 'GET':
        return redirect('login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            refresh['first_name'] = user.first_name
            refresh['last_name'] = user.last_name
            refresh['email'] = user.email
            refresh['is_staff'] = user.is_staff
            refresh['is_superuser'] = user.is_superuser
            refresh['role'] = user.role
            
            # Определяем URL для перенаправления в зависимости от роли
            if user.role == 'TEACHER':
                redirect_url = 'http://localhost:8004/'
            elif user.role == 'ADMIN':
                redirect_url = 'http://localhost:8002/admin/'
            else:
                redirect_url = 'http://localhost:8003/'
            
            response = redirect(redirect_url)
            response.set_cookie(
                'token',
                str(refresh.access_token),
                max_age=3600,
                httponly=True,
                samesite='Lax'
            )
            return response
        else:
            return render(request, 'auth/login.html', {
                'error': 'Неверное имя пользователя или пароль'
            })

def token_verify(request):
    return TokenVerifyView.as_view()(request)

@csrf_protect
def logout_view(request):
    logout(request)
    response = redirect('login')
    response.delete_cookie('token')
    return response
