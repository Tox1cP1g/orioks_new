from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SemesterViewSet, SubjectViewSet, GradeViewSet, ScheduleViewSet,
    AttendanceViewSet, StudentViewSet, add_grade_view, subjects, assignments, news,
    TeacherViewSet as TeacherModelViewSet,
    SubjectTeacherViewSet, 
    live_subject_teachers
)
from .api_views import (
    TeacherViewSet as APITeacherViewSet, 
    SubjectViewSet as APISubjectViewSet,
    GroupStudentsAPIView, get_subject_teachers, get_teacher_subjects
)
from .api_views import create_user_profile, get_groups, get_student_info, update_student_group


router = DefaultRouter()
router.register(r'semesters', SemesterViewSet)
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'schedule', ScheduleViewSet, basename='schedule')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'teachers', TeacherModelViewSet, basename='teacher')
router.register(r'subject-teachers', SubjectTeacherViewSet, basename='subject-teacher')

# API роутеры
api_router = DefaultRouter()
api_router.register(r'teachers-api', APITeacherViewSet, basename='teacher-api')
api_router.register(r'subjects-api', APISubjectViewSet, basename='subject-api')

urlpatterns = [
    path('subjects/', subjects, name='subjects'),
    path('assignments/', assignments, name='assignments'),
    path('news/', news, name='news'),
    path('add-grade/', add_grade_view, name='add_grade'),
    path('teacher-subjects/', live_subject_teachers, name='live_subject_teachers'),
    
    # API пути
    path('api/create-profile/', create_user_profile, name='create_profile'),
    path('api/groups/', get_groups, name='get_groups'),
    path('api/students/<int:user_id>/', get_student_info, name='get_student_info'),
    path('api/students/<int:user_id>/update-group/', update_student_group, name='update_student_group'),
    
    # Новые API пути для интеграции студент-преподаватель
    path('api/subject/<int:subject_id>/teachers/', get_subject_teachers, name='api_subject_teachers'),
    path('api/teacher/<int:teacher_id>/subjects/', get_teacher_subjects, name='api_teacher_subjects'),
    path('api/group/<int:pk>/students/', GroupStudentsAPIView.as_view(), name='api_group_students'),
    
    # Включаем старый API 
    path('', include(router.urls)),
    
    # Включаем новый API
    path('api/', include(api_router.urls)),
]
