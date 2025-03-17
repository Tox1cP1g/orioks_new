from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubjectViewSet,
    GradeViewSet,
    ScheduleViewSet,
    AttendanceViewSet,
    StudentViewSet
)

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'schedule', ScheduleViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'students', StudentViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 