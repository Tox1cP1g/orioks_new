from django.urls import path
from django.contrib.auth import views as auth_views
from .views import student_login
from . import templates
from . import views

urlpatterns = [
    path('login/', views.login_choice, name='login_choice'),  # Страница выбора
    path('login/student', student_login, name='student_login'),
    path('login/staff/', views.staff_login, name='staff_login'),  # Вход для сотрудников
    # path('logout/confirm/', auth_views.LogoutView.as_view(template_name='logout_confirm.html'), name='logout_confirm'),
    path('logout/', views.UserLogoutView.as_view(http_method_names=['get', 'post', 'options']), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    # path('profile/', views.profile_view, name='profile'),

]
