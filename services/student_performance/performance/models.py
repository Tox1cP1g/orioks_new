from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

User = get_user_model()

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

class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('HW', 'Домашнее задание'),
        ('LAB', 'Лабораторная работа'),
        ('TEST', 'Контрольная работа'),
        ('EXAM', 'Экзамен'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200, verbose_name="Название задания")
    description = models.TextField(verbose_name="Описание задания")
    type = models.CharField(max_length=4, choices=ASSIGNMENT_TYPES, verbose_name="Тип задания")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Максимальный балл")
    deadline = models.DateTimeField(verbose_name="Срок сдачи")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
        ordering = ['deadline']

    def __str__(self):
        return f"{self.get_type_display()} - {self.title}"

class StudentAssignment(models.Model):
    STATUS_CHOICES = [
        ('NOT_SUBMITTED', 'Не сдано'),
        ('SUBMITTED', 'На проверке'),
        ('RETURNED', 'На доработке'),
        ('COMPLETED', 'Выполнено'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_SUBMITTED')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    submission_text = models.TextField(blank=True, verbose_name="Текст ответа")
    submission_file = models.FileField(upload_to='submissions/', null=True, blank=True, verbose_name="Файл с решением")
    feedback = models.TextField(blank=True, verbose_name="Комментарий преподавателя")
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Задание студента"
        verbose_name_plural = "Задания студентов"
        unique_together = ['student', 'assignment']

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

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

class Subject(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название предмета")
    code = models.CharField(max_length=20, verbose_name="Код предмета")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects', verbose_name="Семестр")
    credits = models.PositiveSmallIntegerField(verbose_name="Кредиты")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

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
    group = models.CharField(max_length=50, verbose_name="Группа")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='schedule_items', verbose_name="Семестр")

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"
        ordering = ['day_of_week', 'lesson_number']
        unique_together = ['day_of_week', 'lesson_number', 'room', 'semester']

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.get_lesson_number_display()} - {self.subject}"

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

class Group(models.Model):
    """Модель группы студентов"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы")
    faculty = models.CharField(max_length=100, verbose_name="Факультет")
    course = models.IntegerField(verbose_name="Курс")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ['course', 'name']

    def __str__(self):
        return f"{self.name} ({self.faculty}, {self.course} курс)"

class Student(models.Model):
    """Модель студента"""
    user_id = models.IntegerField(unique=True, verbose_name="ID пользователя")
    student_number = models.CharField(max_length=50, unique=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    faculty = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} ({self.student_number})"

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"
        ordering = ['student_number']

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

class HomeworkAssignment(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    name = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-deadline']

    def __str__(self):
        return f"{self.subject.name} - {self.name}"

class HomeworkSubmission(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Отправлено'),
        ('CHECKING', 'На проверке'),
        ('GRADED', 'Оценено'),
        ('REJECTED', 'Отклонено')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homework_submissions')
    assignment = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE, related_name='submissions')
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='homework_submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.user_id} - {self.assignment.name}"

    class Meta:
        ordering = ['-submitted_at'] 