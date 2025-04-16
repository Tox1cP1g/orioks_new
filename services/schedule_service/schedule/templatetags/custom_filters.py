from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_lesson_type(schedule):
    """Возвращает тип занятия (лекция/практика)"""
    return "Лекция" if schedule.is_lecture else "Практика"

@register.filter
def get_lesson_time(lesson_number):
    """Возвращает время проведения занятия"""
    times = {
        1: "9:00-10:30",
        2: "10:45-12:15",
        3: "13:00-14:30",
        4: "14:45-16:15",
        5: "16:30-18:00",
        6: "18:15-19:45"
    }
    return times.get(lesson_number, "")

@register.filter
def get_day_name(day_number):
    """Возвращает название дня недели"""
    days = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота",
        7: "Воскресенье"
    }
    return days.get(day_number, "") 