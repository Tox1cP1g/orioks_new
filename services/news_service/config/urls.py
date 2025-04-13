from django.urls import path, include

urlpatterns = [
    path('', include('news.urls')),  # Основной маршрут новостей
]