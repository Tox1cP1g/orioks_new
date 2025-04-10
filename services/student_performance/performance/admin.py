from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Semester, Subject, Grade, Schedule, 
    Attendance, Group, Student, UserProfile,
    SubjectGroup
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профиль'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_group')
    
    def get_group(self, obj):
        return obj.profile.student_group if hasattr(obj, 'profile') and obj.profile.student_group else 'Без группы'
    get_group.short_description = 'Группа'

# Перерегистрируем модель User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class SubjectGroupInline(admin.TabularInline):
    model = SubjectGroup
    extra = 1

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester', 'credits', 'get_groups')
    list_filter = ('semester', 'credits', 'groups')
    search_fields = ('name', 'code')
    inlines = [SubjectGroupInline]

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = 'Группы'

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'course', 'created_at')
    list_filter = ('faculty', 'course')
    search_fields = ('name', 'faculty')
    ordering = ['name']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_number', 'group', 'faculty')
    list_filter = ('group', 'faculty')
    search_fields = ('student_number', 'group__name')
    ordering = ['student_number']

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'subject', 'grade_type', 'score', 'max_score', 'date')
    list_filter = ('grade_type', 'subject', 'date')
    search_fields = ('student_id', 'subject__name')
    date_hierarchy = 'date'

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'get_day_of_week_display', 'get_lesson_number_display', 'room', 'teacher', 'is_lecture', 'group')
    list_filter = ('day_of_week', 'is_lecture', 'semester', 'group')
    search_fields = ('subject__name', 'teacher', 'room', 'group__name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'schedule_item', 'date', 'is_present')
    list_filter = ('is_present', 'date', 'schedule_item__subject')
    search_fields = ('student_id', 'schedule_item__subject__name')
    date_hierarchy = 'date'

@admin.register(SubjectGroup)
class SubjectGroupAdmin(admin.ModelAdmin):
    list_display = ('subject', 'group', 'teacher', 'is_lecture')
    list_filter = ('group', 'is_lecture', 'subject')
    search_fields = ('subject__name', 'group__name', 'teacher') 