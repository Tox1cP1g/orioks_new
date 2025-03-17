from django.urls import path
from .views import RegisterView, UserDetailView, get_user_info

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('user/info/', get_user_info, name='user-info'),
] 