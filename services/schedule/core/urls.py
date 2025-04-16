from django.urls import path, include
from . import views
from django.contrib import admin

# Маршруты из старого schedule/urls.py
main_patterns = [
    path('', views.schedule_view, name='schedule'),
]

# Маршруты из старого api/urls.py
api_patterns = [
    path('schedule/', views.ScheduleView.as_view(), name='api-schedule'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(main_patterns)),
    path('api/', include(api_patterns)),
]