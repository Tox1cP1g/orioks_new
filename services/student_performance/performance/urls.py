from django.urls import path, include
from rest_framework.routers import DefaultRouter
<<<<<<< Updated upstream
from .views import SemesterViewSet, SubjectViewSet, GradeViewSet, ScheduleViewSet, AttendanceViewSet, StudentViewSet
from .api_views import create_user_profile
=======
from .views import (
    SemesterViewSet, SubjectViewSet, GradeViewSet,
    ScheduleViewSet, AttendanceViewSet, StudentViewSet
)
>>>>>>> Stashed changes

router = DefaultRouter()
router.register(r'semesters', SemesterViewSet)
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'schedule', ScheduleViewSet, basename='schedule')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'students', StudentViewSet, basename='student')

urlpatterns = [
    path('', include(router.urls)),
    path('api/create-profile/', create_user_profile, name='create_profile'),
] 