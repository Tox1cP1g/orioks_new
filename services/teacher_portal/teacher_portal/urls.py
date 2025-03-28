"""teacher_portal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from teaching.views import DashboardView, logout_view, profile, courses, assignments, submissions, grade_submission, create_course, create_assignment

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('api/', include('teaching.urls')),
    path('profile/', profile, name='profile'),
    path('courses/', courses, name='courses'),
    path('create-course/', create_course, name='create_course'),
    path('submissions/', submissions, name='submissions'),
    path('submissions/grade/<int:submission_id>/', grade_submission, name='grade_submission'),
    path('assignments/', assignments, name='assignments'),
    path("assignments/", assignments, name="assignments_list"),
    path("assignments/create/", create_assignment, name="assignment_form"),
    path('logout/', logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
