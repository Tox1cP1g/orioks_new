from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('STUDENT', 'Студент'),
        ('TEACHER', 'Преподаватель'),
        ('ADMIN', 'Администратор'),
    ]
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='STUDENT',
        verbose_name="Роль пользователя"
    )
    student_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер студенческого")
    department = models.CharField(max_length=200, blank=True, null=True, verbose_name="Кафедра")
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="Должность")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})" 