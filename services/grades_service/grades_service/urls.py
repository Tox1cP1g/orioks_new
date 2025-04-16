"""
URL configuration for grades_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.views.generic import RedirectView

from grades.views import (
    index, teacher_grades, student_grades, get_student_grades,
    get_groups, get_grades, logout, direct_to_teacher_portal,
    direct_to_student_portal, test_redirect, edit_grade,
    add_grade, delete_grade, set_student_group, sync_data_from_portals
)

from grades.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    
    # Основные URL
    path('', index, name='index'),
    path('teacher-grades/', teacher_grades, name='teacher_grades'),
    path('student-grades/', student_grades, name='student_grades'),
    path('logout/', logout, name='logout'),
    path('test-redirect/', test_redirect, name='test_redirect'),
    
    # API endpoints
    path('api/student/grades/<int:semester_id>/', get_student_grades, name='get_student_grades'),
    path('api/groups/<int:semester_id>/', get_groups, name='get_groups'),
    path('api/grades/<int:group_id>/', get_grades, name='get_grades'),
    path('api/grades/', add_grade, name='add_grade'),
    path('api/grades/<int:grade_id>/', delete_grade, name='delete_grade'),
    path('api/student/set-group/', set_student_group, name='set_student_group'),
    
    # Редактирование оценки
    path('edit-grade/<int:grade_id>/', edit_grade, name='edit_grade'),
    
    # Административные функции
    path('admin/sync-data/', sync_data_from_portals, name='sync_data_from_portals'),
    
    # Специальные маршруты для перехвата запросов на другие порты
    re_path(r'.*8004.*', direct_to_teacher_portal, name='direct_to_teacher_portal'),
    re_path(r'.*8003.*', direct_to_student_portal, name='direct_to_student_portal'),
    re_path(r'.*4004.*', direct_to_teacher_portal, name='direct_to_teacher_portal_dev'),
    re_path(r'.*4003.*', direct_to_student_portal, name='direct_to_student_portal_dev'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
