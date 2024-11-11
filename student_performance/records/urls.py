from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.student_list, name='student_list'),
    path('courses/', views.course_list, name='course_list'),
    path('grades/', views.grade_list, name='grade_list'),
    # path('report/', views.create_report),
    path('report/', views.student_report_view, name='student_report'),
    path('grades/', views.grades_view, name='grades'),
    path('grades_info/', views.grades_info, name='grades_info'),
    path('subjects_info/', views.subjects_list, name='subjects_list')
]
