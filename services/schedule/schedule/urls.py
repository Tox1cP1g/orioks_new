from django.urls import path, include
from django.contrib import admin
from api.views import schedule_view  # Абсолютный импорт

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', schedule_view, name='schedule'),
    path('api/', include('api.urls')),
]