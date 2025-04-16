from django.contrib import admin
from .models import (
    Student, Subject, Grade, Schedule,
    Attendance, Semester, HomeworkAssignment,
    HomeworkSubmission, Group, Teacher, SubjectTeacher
)

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester', 'credits')
    list_filter = ('semester', 'credits')
    search_fields = ('name', 'code')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'subject', 'grade_type', 'score', 'max_score', 'date')
    list_filter = ('grade_type', 'subject', 'date')
    search_fields = ('student_id', 'subject__name')
    date_hierarchy = 'date'

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'get_day_of_week_display', 'get_lesson_number_display', 'room', 'teacher', 'is_lecture', 'group')
    list_filter = ('day_of_week', 'is_lecture', 'semester')
    search_fields = ('subject__name', 'teacher', 'room', 'group')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'schedule_item', 'date', 'is_present')
    list_filter = ('is_present', 'date', 'schedule_item__subject')
    search_fields = ('student_id', 'schedule_item__subject__name')
    date_hierarchy = 'date'

@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'deadline')
    list_filter = ('subject', 'deadline')
    search_fields = ('name', 'description', 'subject__name')
    ordering = ('-deadline',)

@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'submitted_at', 'grade')
    list_filter = ('status', 'submitted_at', 'assignment__subject')
    search_fields = ('student__user_id', 'assignment__name')
    date_hierarchy = 'submitted_at'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'student_number', 'group', 'faculty')
    list_filter = ('group', 'faculty')
    search_fields = ('user_id', 'student_number', 'group__name')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'course')
    list_filter = ('faculty', 'course')
    search_fields = ('name', 'faculty')
    ordering = ('course', 'name')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'last_name', 'first_name', 'department', 'position', 'email')
    list_filter = ('department', 'position', 'academic_degree')
    search_fields = ('user_id', 'last_name', 'first_name', 'department')
    ordering = ('last_name', 'first_name')

@admin.register(SubjectTeacher)
class SubjectTeacherAdmin(admin.ModelAdmin):
    list_display = ('subject', 'teacher', 'role', 'is_main')
    list_filter = ('role', 'is_main', 'subject')
    search_fields = ('subject__name', 'teacher__last_name', 'teacher__first_name')
    ordering = ('subject', '-is_main', 'role') 