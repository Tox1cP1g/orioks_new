from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=200, verbose_name="Кафедра")
    position = models.CharField(max_length=100, verbose_name="Должность")
    academic_degree = models.CharField(max_length=100, blank=True, verbose_name="Ученая степень")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    office_hours = models.TextField(blank=True, verbose_name="Часы консультаций")

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"

class Course(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название курса")
    description = models.TextField(verbose_name="Описание курса")
    teachers = models.ManyToManyField(Teacher, related_name='courses', verbose_name="Преподаватели")
    semester = models.IntegerField(verbose_name="Семестр")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['-semester', 'name']

    def __str__(self):
        return f"{self.name} (Семестр {self.semester})"

class LearningMaterial(models.Model):
    MATERIAL_TYPES = [
        ('LECTURE', 'Лекция'),
        ('PRACTICE', 'Практика'),
        ('LAB', 'Лабораторная работа'),
        ('ADDITIONAL', 'Дополнительные материалы'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200, verbose_name="Название")
    type = models.CharField(max_length=20, choices=MATERIAL_TYPES, verbose_name="Тип материала")
    content = models.TextField(verbose_name="Содержание")
    file = models.FileField(upload_to='materials/', null=True, blank=True, verbose_name="Файл")
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Учебный материал"
        verbose_name_plural = "Учебные материалы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} - {self.title}"

class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('HW', 'Домашнее задание'),
        ('LAB', 'Лабораторная работа'),
        ('TEST', 'Контрольная работа'),
        ('EXAM', 'Экзамен'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
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

class GradingCriteria(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='criteria')
    description = models.CharField(max_length=200, verbose_name="Описание критерия")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Максимальный балл")
    
    class Meta:
        verbose_name = "Критерий оценивания"
        verbose_name_plural = "Критерии оценивания"

    def __str__(self):
        return f"{self.assignment.title} - {self.description}"

class StudentSubmission(models.Model):
    STATUS_CHOICES = [
        ('NOT_SUBMITTED', 'Не сдано'),
        ('SUBMITTED', 'На проверке'),
        ('RETURNED', 'На доработке'),
        ('COMPLETED', 'Проверено'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student_id = models.IntegerField(verbose_name="ID студента")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_SUBMITTED')
    submission_text = models.TextField(blank=True, verbose_name="Текст ответа")
    files = models.FileField(upload_to='submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Ответ студента"
        verbose_name_plural = "Ответы студентов"
        unique_together = ['assignment', 'student_id']

    def __str__(self):
        return f"Ответ на {self.assignment.title} от студента {self.student_id}"

class Grade(models.Model):
    submission = models.OneToOneField(StudentSubmission, on_delete=models.CASCADE, related_name='grade')
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Балл")
    feedback = models.TextField(verbose_name="Комментарий преподавателя")
    graded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"

    def __str__(self):
        return f"Оценка {self.score} за {self.submission.assignment.title}"

class Subject(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название предмета")
    description = models.TextField(blank=True, verbose_name="Описание")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='subjects', verbose_name="Преподаватель")
    semester = models.IntegerField(verbose_name="Семестр")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['-semester', 'name']

    def __str__(self):
        return self.name

class Group(models.Model):
    """Модель академической группы"""
    name = models.CharField(max_length=20, unique=True, verbose_name="Название группы")
    faculty = models.CharField(max_length=100, verbose_name="Факультет", blank=True)
    year = models.PositiveSmallIntegerField(verbose_name="Год обучения", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ['name']
    
    def __str__(self):
        return self.name

# Роли преподавателей для предмета
TEACHER_ROLES = [
    ('LECTURER', 'Лектор'),
    ('PRACTICE', 'Руководитель практики'),
    ('ASSISTANT', 'Ассистент'),
    ('TUTOR', 'Куратор'),
    ('LAB', 'Лабораторные работы'),
]

class SubjectTeacher(models.Model):
    """
    Модель связи между предметом и преподавателем.
    Определяет, какие преподаватели ведут какие предметы.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teachers', verbose_name='Предмет')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='subject_teachers', verbose_name='Преподаватель')
    role = models.CharField(max_length=20, choices=TEACHER_ROLES, default='LECTURER', verbose_name='Роль')
    is_main = models.BooleanField(default=False, verbose_name='Основной преподаватель')
    groups = models.ManyToManyField(Group, related_name='subject_teachers', verbose_name='Группы')
    
    class Meta:
        verbose_name = 'Связь предмет-преподаватель'
        verbose_name_plural = 'Связи предмет-преподаватель'
        unique_together = ['subject', 'teacher', 'role']

    def __str__(self):
        return f"{self.teacher} - {self.subject} ({self.get_role_display()})"

class SubjectTeacherGroup(models.Model):
    """
    Устаревшая модель связи между преподавателем предмета и группой.
    Заменена на ManyToMany поле groups в модели SubjectTeacher.
    """
    subject_teacher = models.ForeignKey(SubjectTeacher, on_delete=models.CASCADE, 
                                        related_name='old_groups', verbose_name='Связь предмет-преподаватель')
    group_code = models.CharField(max_length=20, verbose_name='Код группы')
    
    class Meta:
        verbose_name = 'Группа преподавателя предмета (устарело)'
        verbose_name_plural = 'Группы преподавателей предметов (устарело)'
        unique_together = ['subject_teacher', 'group_code']
        
    def __str__(self):
        return f"{self.subject_teacher} - Группа {self.group_code}"

class StudentAssignment(models.Model):
    STATUS_CHOICES = [
        ('not_submitted', 'Не сдано'),
        ('submitted', 'На проверке'),
        ('returned', 'На доработке'),
        ('completed', 'Проверено'),
    ]

    student = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='assignments', verbose_name="Студент")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='student_assignments', verbose_name="Задание")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_submitted', verbose_name="Статус")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата сдачи")
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Оценка")
    feedback = models.TextField(blank=True, verbose_name="Комментарий преподавателя")

    class Meta:
        verbose_name = "Задание студента"
        verbose_name_plural = "Задания студентов"
        ordering = ['-submitted_at']
        unique_together = ['student', 'assignment']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"

class Schedule(models.Model):
    DAYS_OF_WEEK = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    ]

    LESSON_NUMBERS = [
        (1, '1 пара (9:00-10:30)'),
        (2, '2 пара (10:40-12:10)'),
        (3, '3 пара (12:20-13:50)'),
        (4, '4 пара (14:30-16:00)'),
        (5, '5 пара (16:10-17:40)'),
        (6, '6 пара (17:50-19:20)'),
        (7, '7 пара (19:30-21:00)'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedule_items', verbose_name="Предмет")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedule_items', verbose_name="Преподаватель")
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="День недели")
    lesson_number = models.IntegerField(choices=LESSON_NUMBERS, verbose_name="Номер пары")
    room = models.CharField(max_length=50, verbose_name="Аудитория")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"
        ordering = ['day_of_week', 'lesson_number']
        unique_together = ['subject', 'day_of_week', 'lesson_number']

    def __str__(self):
        return f"{self.subject.name} - {self.get_day_of_week_display()} {self.get_lesson_number_display()}"

class Attendance(models.Model):
    schedule_item = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='attendances', verbose_name="Занятие")
    student = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='attendances', verbose_name="Студент")
    date = models.DateField(verbose_name="Дата")
    is_present = models.BooleanField(default=False, verbose_name="Присутствовал")
    note = models.TextField(blank=True, verbose_name="Примечание")

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        ordering = ['-date', 'schedule_item__lesson_number']
        unique_together = ['schedule_item', 'student', 'date']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.schedule_item} ({self.date})"

class HomeworkSubmission(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Отправлено'),
        ('REVIEWING', 'На проверке'),
        ('GRADED', 'Оценено'),
        ('REJECTED', 'Отклонено')
    ]

    submission_id = models.IntegerField(unique=True)  # ID из сервиса студента
    student_name = models.CharField(max_length=255)
    assignment_name = models.CharField(max_length=255)
    subject_name = models.CharField(max_length=255)
    received_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.student_name} - {self.assignment_name} ({self.subject_name})"

    def save(self, *args, **kwargs):
        if self.grade and not self.graded_at:
            self.graded_at = timezone.now()
            self.status = 'GRADED'
        super().save(*args, **kwargs)
