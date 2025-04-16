from django.contrib import admin
from .models import Schedule, Group

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'lesson_number', 'subject', 'teacher', 'room', 'group', 'semester', 'is_lecture')
    list_filter = ('day_of_week', 'semester', 'group', 'is_lecture')
    search_fields = ('subject', 'teacher', 'room', 'group__name')
    ordering = ('day_of_week', 'lesson_number') 