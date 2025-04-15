from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    StudentViewSet, SubjectViewSet, GradeViewSet, SemesterViewSet
)

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'semesters', SemesterViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
] 