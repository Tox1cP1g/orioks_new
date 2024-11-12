from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('students/', views.student_list, name='student_list'),
    path('courses/', views.course_list, name='course_list'),
    path('grades/', views.grade_list, name='grade_list'),
    # path('report/', views.create_report),
    path('report/', views.student_report_view, name='student_report'),
    path('grades/', views.grades_view, name='grades'),
    path('grades_info/', views.grades_info, name='grades_info'),
    path('subjects/', views.subjects_list, name='subjects_list'),
    path('internships/', views.internship_list, name='internships'),
    path('homework/create/', views.create_homework, name='create_homework'),
    path('homework/', views.homework_list, name='homework_list'),
    path('profile/', views.profile, name='profile'),
    path('profile_staff/', views.profile_staff, name='profile_staff'),
    path('help_students', views.help_students, name='help_students'),
    path('schedule/', views.schedule_view, name='schedule'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)