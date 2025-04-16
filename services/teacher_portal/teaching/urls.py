from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    SubjectViewSet,
    GradeViewSet,
    ScheduleViewSet,
    AttendanceViewSet,
    StudentViewSet,
    TeacherViewSet,
    SubjectTeacherViewSet,
    public_teachers_api,
    raw_json_teachers_api,
)
from . import views

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'schedule', ScheduleViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'students', StudentViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'subject-teachers', SubjectTeacherViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', views.dashboard, name='dashboard'),
    path('homework/', views.homework, name='homework'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    
    # Публичный API доступный без аутентификации
    path('public-teacher-subjects/', public_teachers_api, name='public_teacher_subjects'),
    path('public-teacher-subjects.json', public_teachers_api, name='public_teacher_subjects_json'),
    path('api/public/teachers/', public_teachers_api, name='public_teachers_api'),
    # Новый гарантированный JSON API
    path('raw-json-api/teachers/', raw_json_teachers_api, name='raw_json_teachers_api'),
    path('api/v1/public/data.json', public_teachers_api, name='data_json_api'),
    
    # JWT аутентификация
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 