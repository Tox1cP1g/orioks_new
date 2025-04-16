from django.contrib import admin
from .models import (
    Teacher, Course, LearningMaterial, Assignment,
    GradingCriteria, StudentSubmission, Grade,
    Subject, SubjectTeacher, Schedule, Attendance,
    Group
)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'position', 'academic_degree')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department')
    list_filter = ('department', 'position')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'semester', 'created_at')
    search_fields = ('name', 'teacher__user__first_name', 'teacher__user__last_name')
    list_filter = ('semester',)
    
@admin.register(SubjectTeacher)
class SubjectTeacherAdmin(admin.ModelAdmin):
    list_display = ('subject', 'teacher', 'role', 'is_main')
    search_fields = ('subject__name', 'teacher__user__first_name', 'teacher__user__last_name')
    list_filter = ('role', 'is_main')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('semester', 'created_at')
    filter_horizontal = ('teachers',)

@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'type', 'created_by', 'created_at')
    search_fields = ('title', 'content', 'course__name')
    list_filter = ('type', 'created_at')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'type', 'max_score', 'deadline')
    search_fields = ('title', 'description', 'course__name')
    list_filter = ('type', 'deadline', 'created_at')

@admin.register(GradingCriteria)
class GradingCriteriaAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'description', 'max_score')
    search_fields = ('description', 'assignment__title')
    list_filter = ('assignment__course',)

@admin.register(StudentSubmission)
class StudentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student_id', 'status', 'submitted_at')
    search_fields = ('student_id', 'submission_text', 'assignment__title')
    list_filter = ('status', 'submitted_at')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('submission', 'graded_by', 'score', 'graded_at')
    search_fields = ('feedback', 'submission__student_id')
    list_filter = ('graded_at', 'score')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'year', 'created_at')
    search_fields = ('name', 'faculty')
    list_filter = ('year',)
