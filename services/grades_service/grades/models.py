from django.db import models
from django.utils import timezone

class Semester(models.Model):
    """Модель семестра"""
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date']

class Group(models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.name

class Teacher(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    department = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=100, blank=True)
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return f"Teacher {self.user_id}"
    
    def __str__(self):
        return self.get_full_name()

class Subject(models.Model):
    """Модель предмета"""
    name = models.CharField(max_length=255)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Student(models.Model):
    """Модель студента"""
    user_id = models.CharField(max_length=100, unique=True, default='')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, related_name='students')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return f"Student {self.user_id}"

    def __str__(self):
        return self.get_full_name()

    class Meta:
        ordering = ['last_name', 'first_name']

class Grade(models.Model):
    """Модель оценки"""
    GRADE_TYPES = [
        ('homework', 'Домашняя работа'),
        ('lab', 'Лабораторная работа'),
        ('test', 'Тест'),
        ('exam', 'Экзамен'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPES)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(default=timezone.now)
    comment = models.TextField(blank=True)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.score}/{self.max_score}"

    class Meta:
        ordering = ['-date']
