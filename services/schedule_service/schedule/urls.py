from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule_list, name='schedule_list'),
    path('add/', views.add_schedule, name='add_schedule'),
    path('<int:schedule_id>/', views.schedule_detail, name='schedule_detail'),
    path('<int:schedule_id>/edit/', views.edit_schedule, name='edit_schedule'),
    path('<int:schedule_id>/delete/', views.delete_schedule, name='delete_schedule'),
    path('api/group/', views.get_or_create_group, name='get_or_create_group'),
] 