from django.contrib import admin
from .models import Group, Schedule

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Убрали 'faculty', так как его нет в модели
    search_fields = ('name',)  # Поиск только по имени группы

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'day', 'subject', 'teacher', 'classroom', 'start_time', 'end_time')
    list_filter = ('group', 'day')  # Фильтрация только по существующим полям
    search_fields = ('subject', 'teacher', 'classroom')
    ordering = ('group', 'day', 'start_time')  # Сортировка по существующим полям