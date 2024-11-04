from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.student_list, name='student_list'),
    path('courses/', views.course_list, name='course_list'),
    path('grades/', views.grade_list, name='grade_list'),
    path('report/', views.create_report)

]
