from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)  # Описание может быть необязательным

    def __str__(self):
        return self.name


class Student(models.Model):
    FORM_OF_EDUCATION_CHOICES = [
        ('Очная', 'Очная'),
        ('Очно-заочная', 'Очно-заочная'),
        ('Заочная', 'Заочная'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # например, ID существующего пользователя
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)  # Поле может быть пустым
    enrollment_date = models.DateField()  # Дата зачисления обязательна
    student_id = models.CharField(max_length=20, unique=True)  # Убираем null=True и blank=True
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # Временно сделаем поле необязательным
    form_of_education = models.CharField(max_length=20, choices=FORM_OF_EDUCATION_CHOICES, default='Очная')  # Значение по умолчанию
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # Телефон можно сделать необязательным
    email = models.EmailField(blank=True, null=True)  # Электронную почту можно сделать необязательной

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}"


class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, default='Неизвестный Преподаватель')  # Значение по умолчанию

    def __str__(self):
        return self.full_name


class Course(models.Model):
    FORM_OF_CONTROL_CHOICES = [
        ('Экзамен', 'Экзамен'),
        ('Зачет', 'Зачет'),
        ('Дифференцированный зачет', 'Дифференцированный зачет'),
        ('Курсовая работа', 'Курсовая работа'),
    ]

    name = models.CharField(max_length=100)
    semester = models.IntegerField(default=1)  # Значение по умолчанию
    hours = models.IntegerField(default=36)  # Значение по умолчанию
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, null=True, blank=True)  # Временно сделаем необязательным
    form_of_control = models.CharField(
        max_length=50,
        choices=FORM_OF_CONTROL_CHOICES,
        default='Зачет'  # Значение по умолчанию
    )

    def __str__(self):
        return self.name


class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grade = models.FloatField(default=0.0)  # Значение по умолчанию
    date_of_grade = models.DateField(null=True, blank=True)
    attendance = models.IntegerField(default=100)  # Процент посещаемости по умолчанию

    def __str__(self):
        return f"{self.student} - {self.course}: {self.grade}"


class AcademicPlan(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)
    semester = models.IntegerField(default=1)  # Значение по умолчанию

    def __str__(self):
        return f"Учебный план группы {self.group} на семестр {self.semester}"


class Report(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.IntegerField(default=1)  # Значение по умолчанию
    average_grade = models.FloatField(default=0.0)  # Значение по умолчанию

    def __str__(self):
        return f"Отчет по {self.student} за {self.semester} семестр"


class Internship(models.Model):
    company = models.CharField("Компания", max_length=255)
    company_representative = models.CharField("Представитель компании", max_length=255)
    contact_details = models.TextField("Контактные данные компании")
    is_academic_supervisor = models.BooleanField("Научный руководитель МИЭТ")
    is_company_supervisor = models.BooleanField("Руководитель от предприятия")

    def __str__(self):
        return f"{self.company} - {self.company_representative}"


# from django.db import models


class Homework(models.Model):
    title = models.CharField(max_length=255)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    description = models.TextField()
    due_date = models.DateField()
    files = models.FileField(upload_to='homework_files/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1, related_name='homeworks')  # поле для отправителя

    def __str__(self):
        return self.title


class HomeworkFile(models.Model):
    homework = models.ForeignKey(Homework, related_name='homework_files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='homework_files/', blank=True, null=True)

    def __str__(self):
        return f"File for {self.homework.title}"


class Schedule(models.Model):
    subject = models.CharField(max_length=100, verbose_name="Предмет")
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE, verbose_name="Преподаватель")
    group = models.CharField(max_length=10, verbose_name="Группа")
    day_of_week = models.CharField(
        max_length=12,
        choices=[('Понедельник', 'Понедельник'), ('Вторник', 'Вторник'), ('Среда', 'Среда'),
                 ('Четверг', 'Четверг'), ('Пятница', 'Пятница'), ('Суббота', 'Суббота')],
        verbose_name="День недели"
    )
    time = models.TimeField(verbose_name="Время начала занятия")
    location = models.CharField(max_length=100, verbose_name="Аудитория")

    def __str__(self):
        return f"{self.subject} - {self.group} ({self.day_of_week} {self.time})"