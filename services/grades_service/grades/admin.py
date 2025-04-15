from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from .models import Semester, Group, Student, Teacher, Subject, Grade

class GradesServiceAdminSite(admin.AdminSite):
    site_header = "ОРИОКС - Управление оценками"
    site_title = "Администрирование сервиса оценок"
    index_title = "Панель управления"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sync-data-page/', self.admin_view(self.sync_data_page), name='sync_data_page'),
        ]
        return custom_urls + urls
    
    def sync_data_page(self, request):
        context = {
            **self.each_context(request),
            'title': 'Синхронизация данных',
        }
        return TemplateResponse(request, 'admin/sync_data.html', context)

# Создаём пользовательский админ-сайт
admin_site = GradesServiceAdminSite(name='grades_admin')

@admin.register(Semester, site=admin_site)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)
    ordering = ('-start_date',)
    list_editable = ('is_current',)
    
@admin.register(Group, site=admin_site)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'get_students_count')
    search_fields = ('name', 'department')
    ordering = ('name',)
    
    def get_students_count(self, obj):
        return obj.students.count()
    get_students_count.short_description = 'Кол-во студентов'

@admin.register(Student, site=admin_site)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'user_id', 'email', 'group')
    list_filter = ('group',)
    search_fields = ('first_name', 'last_name', 'email', 'user_id')
    ordering = ('last_name', 'first_name')
    list_select_related = ('group',)

@admin.register(Teacher, site=admin_site)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'user_id', 'email', 'department', 'position')
    list_filter = ('department', 'position')
    search_fields = ('first_name', 'last_name', 'email', 'user_id')
    ordering = ('last_name', 'first_name')

@admin.register(Subject, site=admin_site)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'teacher', 'created_at')
    list_filter = ('semester', 'teacher')
    search_fields = ('name', 'description')
    list_select_related = ('semester', 'teacher')
    ordering = ('semester', 'name')

@admin.register(Grade, site=admin_site)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'grade_type', 'score', 'max_score', 'date')
    list_filter = ('grade_type', 'subject', 'date')
    search_fields = ('student__first_name', 'student__last_name', 'subject__name')
    list_select_related = ('student', 'subject')
    ordering = ('-date',)
    
    fieldsets = (
        ('Информация о студенте', {
            'fields': ('student',)
        }),
        ('Информация о предмете', {
            'fields': ('subject',)
        }),
        ('Детали оценки', {
            'fields': ('grade_type', 'score', 'max_score', 'date', 'comment')
        }),
        ('Служебная информация', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )

# Добавляем информацию для использования в шаблоне
def get_admin_context(request):
    return {
        'sync_url': reverse('sync_data_from_portals'),
    }
