from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubjectViewSet,
    GradeViewSet,
    ScheduleViewSet,
    AttendanceViewSet,
    StudentViewSet
)
from . import views

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'schedule', ScheduleViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'students', StudentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', views.dashboard, name='dashboard'),
    path('students/', views.students_list, name='students_list'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('grades/', views.grades, name='grades'),
    path('schedule/', views.schedule, name='schedule'),
    path('homework/', views.homework, name='homework'),
    path('profile/', views.profile, name='profile'),
    path('help/', views.help, name='help'),
    path('logout/', views.logout_view, name='logout'),
] 