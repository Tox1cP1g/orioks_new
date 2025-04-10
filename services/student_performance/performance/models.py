from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class Course(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название курса")
    description = models.TextField(verbose_name="Описание курса")
    semester = models.IntegerField(verbose_name="Семестр")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['-semester', 'name']

    def __str__(self):
        return f"{self.name} (Семестр {self.semester})"

class Semester(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название семестра")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    is_current = models.BooleanField(default=False, verbose_name="Текущий семестр")

    class Meta:
        verbose_name = "Семестр"
        verbose_name_plural = "Семестры"
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы")
    faculty = models.CharField(max_length=100, verbose_name="Факультет")
    course = models.IntegerField(verbose_name="Курс")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.faculty}, {self.course} курс)"

class Subject(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название предмета")
    code = models.CharField(max_length=20, verbose_name="Код предмета")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects', verbose_name="Семестр")
    credits = models.PositiveSmallIntegerField(verbose_name="Кредиты")
    description = models.TextField(blank=True, verbose_name="Описание")
    groups = models.ManyToManyField(Group, through='SubjectGroup', related_name='subjects', verbose_name="Группы")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

class SubjectGroup(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    teacher = models.CharField(max_length=200, verbose_name="Преподаватель")
    is_lecture = models.BooleanField(default=True, verbose_name="Лекция")

    class Meta:
        verbose_name = "Предмет группы"
        verbose_name_plural = "Предметы групп"
        unique_together = ['subject', 'group', 'is_lecture']

    def __str__(self):
        return f"{self.subject} - {self.group} ({self.teacher})"

class Student(models.Model):
    user_id = models.IntegerField(unique=True)  # ID from Auth Service
    student_number = models.CharField(max_length=50, unique=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students', verbose_name="Группа")
    faculty = models.CharField(max_length=100, verbose_name="Факультет")

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"
        ordering = ['student_number']

    def __str__(self):
        return f"{self.student_number} ({self.group.name})"

class Schedule(models.Model):
    DAYS_OF_WEEK = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье')
    ]

    LESSON_NUMBERS = [
        (1, '1 пара (9:00-10:30)'),
        (2, '2 пара (10:45-12:15)'),
        (3, '3 пара (13:00-14:30)'),
        (4, '4 пара (14:45-16:15)'),
        (5, '5 пара (16:30-18:00)'),
        (6, '6 пара (18:15-19:45)')
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedule_items', verbose_name="Предмет")
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="День недели")
    lesson_number = models.IntegerField(choices=LESSON_NUMBERS, verbose_name="Номер пары")
    room = models.CharField(max_length=50, verbose_name="Аудитория")
    teacher = models.CharField(max_length=200, verbose_name="Преподаватель")
    is_lecture = models.BooleanField(default=True, verbose_name="Лекция")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='schedule_items', verbose_name="Группа")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='schedule_items', verbose_name="Семестр")

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"
        ordering = ['day_of_week', 'lesson_number']
        unique_together = ['day_of_week', 'lesson_number', 'room', 'semester', 'group']

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.get_lesson_number_display()} - {self.subject} ({self.group.name})"

class Grade(models.Model):
    GRADE_TYPES = [
        ('HW', 'Домашняя работа'),
        ('LAB', 'Лабораторная работа'),
        ('TEST', 'Контрольная работа'),
        ('EXAM', 'Экзамен'),
        ('OTHER', 'Другое')
    ]

    student_id = models.CharField(max_length=50, verbose_name="ID студента")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades', verbose_name="Предмет")
    grade_type = models.CharField(max_length=10, choices=GRADE_TYPES, verbose_name="Тип оценки")
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Балл"
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Максимальный балл"
    )
    date = models.DateField(verbose_name="Дата")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ['-date']

    def __str__(self):
        return f"{self.subject} - {self.get_grade_type_display()} - {self.score}/{self.max_score}"

class Attendance(models.Model):
    student_id = models.CharField(max_length=50, verbose_name="ID студента")
    schedule_item = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='attendances', verbose_name="Занятие")
    date = models.DateField(verbose_name="Дата")
    is_present = models.BooleanField(default=False, verbose_name="Присутствовал")
    reason = models.TextField(blank=True, verbose_name="Причина отсутствия")

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        ordering = ['-date']
        unique_together = ['student_id', 'schedule_item', 'date']

    def __str__(self):
        return f"{self.student_id} - {self.schedule_item} - {self.date}"

class Performance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()
    year = models.IntegerField()
    final_grade = models.DecimalField(max_digits=5, decimal_places=2)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course', 'semester', 'year')
        indexes = [
            models.Index(fields=['student', 'semester', 'year']),
        ]

    def __str__(self):
        return f"{self.student} - {self.course} ({self.semester}/{self.year}): {self.final_grade}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    student_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Группа")
    student_number = models.CharField(max_length=50, blank=True, verbose_name="Номер студенческого")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} - {self.student_group if self.student_group else 'Без группы'}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save() 