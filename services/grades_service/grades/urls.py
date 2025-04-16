from django.urls import path
from . import views

urlpatterns = [
    # API endpoints для студентов
    path('student/grades/<int:semester_id>/', views.get_student_grades, name='get_student_grades'),
    
    # API endpoints для преподавателей
    path('groups/<int:semester_id>/', views.get_groups, name='get_groups'),
    path('grades/<int:group_id>/', views.get_grades, name='get_grades'),
    path('grades/', views.add_grade, name='add_grade'),
    path('grades/<int:grade_id>/', views.delete_grade, name='delete_grade'),
] 