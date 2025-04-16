from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    StudentViewSet, SubjectViewSet, GradeViewSet, SemesterViewSet
)
from .views import (
    get_groups_api,
    get_students_by_group_api,
    get_semesters_api
)

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'semesters', SemesterViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    
    # JSON API endpoints
    path('api/groups.json', get_groups_api, name='json_groups_api'),
    path('api/groups/<int:group_id>/students.json', get_students_by_group_api, name='json_students_by_group_api'),
    path('api/semesters.json', get_semesters_api, name='json_semesters_api'),
] 