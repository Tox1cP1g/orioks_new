from django.db import models
from django.utils import timezone

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        db_table = 'student_performance_group'  # Используем таблицу из основной базы данных

class Schedule(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Понедельник'),
        ('tuesday', 'Вторник'),
        ('wednesday', 'Среда'),
        ('thursday', 'Четверг'),
        ('friday', 'Пятница'),
        ('saturday', 'Суббота'),
    ]

    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK, verbose_name='День недели')
    lesson_number = models.IntegerField(verbose_name='Номер пары')
    subject = models.CharField(max_length=200, verbose_name='Предмет')
    teacher = models.CharField(max_length=200, verbose_name='Преподаватель')
    room = models.CharField(max_length=50, verbose_name='Аудитория')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Группа', to_field='name')
    semester = models.IntegerField(verbose_name='Семестр')
    is_lecture = models.BooleanField(default=False, verbose_name='Лекция')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.lesson_number} пара: {self.subject}"

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['day_of_week', 'lesson_number'] 