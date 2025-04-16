from django.urls import path, include
from . import views
from django.contrib import admin

# Импорты для статических файлов
from django.conf import settings
from django.conf.urls.static import static

# Маршруты из старого schedule/urls.py
main_patterns = [
    path('', views.schedule_view, name='schedule'),
]

# Маршруты из старого api/urls.py
api_patterns = [
    path('schedule/', views.ScheduleView.as_view(), name='api-schedule'),
]

# Основные URL-паттерны
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(main_patterns)),
    path('api/', include(api_patterns)),
]

# Добавляем обработку статических файлов ТОЛЬКО в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)