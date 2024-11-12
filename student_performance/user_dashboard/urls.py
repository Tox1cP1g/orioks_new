from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard_index'),  # маршрут для представления index
    path('staff/', views.index_staff, name='dashboard_staff'),
    path('register/', views.register, name='register'),
    path('phone-directory/', views.phone_directory, name='phone_directory'),  # Добавляем URL для справочника
    path('vote/', views.vote, name='vote'),

]
