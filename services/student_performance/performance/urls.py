from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, StudentViewSet, GradeViewSet, PerformanceViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'students', StudentViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'performance', PerformanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 