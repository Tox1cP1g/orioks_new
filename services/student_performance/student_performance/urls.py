"""
URL configuration for student_performance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter
from performance.views import (
    SemesterViewSet, SubjectViewSet, GradeViewSet,
    ScheduleViewSet, AttendanceViewSet, StudentViewSet,
    index, grades, schedule, help, dashboard, grades_view,
    schedule_view, attendance_view, profile_view, logout_view,

)

router = DefaultRouter()
router.register(r'api/semesters', SemesterViewSet)
router.register(r'api/subjects', SubjectViewSet, basename='subject')
router.register(r'api/grades', GradeViewSet, basename='grade')
router.register(r'api/schedule', ScheduleViewSet, basename='schedule')
router.register(r'api/attendance', AttendanceViewSet, basename='attendance')
router.register(r'api/students', StudentViewSet, basename='student')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('dashboard/', dashboard, name='dashboard'),
    path('grades/', grades_view, name='grades'),
    path('schedule/', schedule_view, name='schedule'),
    path('attendance/', attendance_view, name='attendance'),
    path('help/', help, name='help'),
    path('profile/', profile_view, name='profile'),
    path('logout/', logout_view, name='logout'),
    path('api/', include(router.urls)),
    path('', include('performance.urls')),  # Включаем URL из приложения performance
]
