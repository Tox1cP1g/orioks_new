from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SemesterViewSet, SubjectViewSet, GradeViewSet, ScheduleViewSet,
    AttendanceViewSet, StudentViewSet, add_grade_view, subjects, assignments, news
)
from .api_views import create_user_profile, get_groups, get_student_info, update_student_group


router = DefaultRouter()
router.register(r'semesters', SemesterViewSet)
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'schedule', ScheduleViewSet, basename='schedule')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'students', StudentViewSet, basename='student')

urlpatterns = [
    path('subjects/', subjects, name='subjects'),
    path('assignments/', assignments, name='assignments'),
    path('news/', news, name='news'),
    path('add-grade/', add_grade_view, name='add_grade'),
    path('api/create-profile/', create_user_profile, name='create_profile'),
    path('api/groups/', get_groups, name='get_groups'),
    path('api/students/<int:user_id>/', get_student_info, name='get_student_info'),
    path('api/students/<int:user_id>/update-group/', update_student_group, name='update_student_group'),
    path('', include(router.urls)),
]
