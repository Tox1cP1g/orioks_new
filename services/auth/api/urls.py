from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

urlpatterns = [
    path('api/token/', views.token_obtain_pair, name='token_obtain_pair'),
    path('logout/', views.logout_view, name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
] 