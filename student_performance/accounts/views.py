from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import StudentLoginForm, UserForm, ProfileForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .models import Profile
from records.models import Student  # Импортируем Student из records
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, auth
from django.contrib.auth import logout




# Create your views here.


# from django.contrib.auth.views import LoginView
#
# class CustomLoginView(LoginView):
#     template_name = 'accounts/student_login.html'



@csrf_exempt
def student_login(request):
    if request.method == "POST":
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)  # Аутентификация и вход в систему
                return redirect('/')  # Редирект на главную страницу или страницу профиля
            else:
                form.add_error(None, "Неверное имя пользователя или пароль.")
    else:
        form = StudentLoginForm()

    return render(request, 'student_login.html', {'form': form})


def staff_login(request):
    if request.method == "POST":
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)  # Аутентификация и вход в систему
                return redirect('dashboard_staff')  # Редирект на главную страницу или страницу профиля
            else:
                form.add_error(None, "Неверное имя пользователя или пароль.")
    else:
        form = StudentLoginForm()

    return render(request, 'staff_login.html', {'form': form})

# @login_required
# def profile_view(request):
#     # Получаем студента, связанного с текущим пользователем, или создаем нового, если его нет
#     student, created = Student.objects.get_or_create(user=request.user)
#
#     if request.method == 'POST':
#         user_form = UserForm(request.POST, instance=request.user)
#         profile_form = ProfileForm(request.POST, instance=student)
#
#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             profile_form.save()
#             return redirect('profile')
#     else:
#         user_form = UserForm(instance=request.user)
#         profile_form = ProfileForm(instance=student)
#
#     context = {
#         'user_form': user_form,
#         'profile_form': profile_form,
#         'student': student
#     }
#
#     return render(request, 'accounts/profile.html', context)


def logout_confirm(request):
    return render(request, 'logout_confirm.html')


def login_choice(request):
    return render(request, 'login_choice.html')  # Рендерим страницу выбора


# from django.contrib.auth import logout

from django.contrib.auth import logout
from django.contrib.auth.views import LogoutView

class UserLogoutView(LogoutView):

    def get(self, request):
        logout(request)
        return redirect('login_choice')