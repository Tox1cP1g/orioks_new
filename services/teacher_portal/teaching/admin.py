from django.contrib import admin
from .models import (
    Teacher, Course, LearningMaterial, Assignment,
    GradingCriteria, StudentSubmission, Grade
)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'position', 'academic_degree')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department')
    list_filter = ('position', 'academic_degree')

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
