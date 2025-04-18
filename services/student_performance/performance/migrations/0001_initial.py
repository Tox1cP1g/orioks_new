# Generated by Django 5.1.7 on 2025-04-07 18:14

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название курса')),
                ('description', models.TextField(verbose_name='Описание курса')),
                ('semester', models.IntegerField(verbose_name='Семестр')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Курс',
                'verbose_name_plural': 'Курсы',
                'ordering': ['-semester', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Название группы')),
                ('faculty', models.CharField(max_length=100, verbose_name='Факультет')),
                ('course', models.IntegerField(verbose_name='Курс')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Группа',
                'verbose_name_plural': 'Группы',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название семестра')),
                ('start_date', models.DateField(verbose_name='Дата начала')),
                ('end_date', models.DateField(verbose_name='Дата окончания')),
                ('is_current', models.BooleanField(default=False, verbose_name='Текущий семестр')),
            ],
            options={
                'verbose_name': 'Семестр',
                'verbose_name_plural': 'Семестры',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(unique=True)),
                ('student_number', models.CharField(max_length=50, unique=True)),
                ('faculty', models.CharField(max_length=100, verbose_name='Факультет')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='performance.group', verbose_name='Группа')),
            ],
            options={
                'verbose_name': 'Студент',
                'verbose_name_plural': 'Студенты',
                'ordering': ['student_number'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название предмета')),
                ('code', models.CharField(max_length=20, verbose_name='Код предмета')),
                ('credits', models.PositiveSmallIntegerField(verbose_name='Кредиты')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='performance.semester', verbose_name='Семестр')),
            ],
            options={
                'verbose_name': 'Предмет',
                'verbose_name_plural': 'Предметы',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(choices=[(1, 'Понедельник'), (2, 'Вторник'), (3, 'Среда'), (4, 'Четверг'), (5, 'Пятница'), (6, 'Суббота'), (7, 'Воскресенье')], verbose_name='День недели')),
                ('lesson_number', models.IntegerField(choices=[(1, '1 пара (9:00-10:30)'), (2, '2 пара (10:45-12:15)'), (3, '3 пара (13:00-14:30)'), (4, '4 пара (14:45-16:15)'), (5, '5 пара (16:30-18:00)'), (6, '6 пара (18:15-19:45)')], verbose_name='Номер пары')),
                ('room', models.CharField(max_length=50, verbose_name='Аудитория')),
                ('teacher', models.CharField(max_length=200, verbose_name='Преподаватель')),
                ('is_lecture', models.BooleanField(default=True, verbose_name='Лекция')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_items', to='performance.group', verbose_name='Группа')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_items', to='performance.semester', verbose_name='Семестр')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_items', to='performance.subject', verbose_name='Предмет')),
            ],
            options={
                'verbose_name': 'Расписание',
                'verbose_name_plural': 'Расписание',
                'ordering': ['day_of_week', 'lesson_number'],
                'unique_together': {('day_of_week', 'lesson_number', 'room', 'semester', 'group')},
            },
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=50, verbose_name='ID студента')),
                ('grade_type', models.CharField(choices=[('HW', 'Домашняя работа'), ('LAB', 'Лабораторная работа'), ('TEST', 'Контрольная работа'), ('EXAM', 'Экзамен'), ('OTHER', 'Другое')], max_length=10, verbose_name='Тип оценки')),
                ('score', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Балл')),
                ('max_score', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Максимальный балл')),
                ('date', models.DateField(verbose_name='Дата')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='performance.subject', verbose_name='Предмет')),
            ],
            options={
                'verbose_name': 'Оценка',
                'verbose_name_plural': 'Оценки',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='SubjectGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teacher', models.CharField(max_length=200, verbose_name='Преподаватель')),
                ('is_lecture', models.BooleanField(default=True, verbose_name='Лекция')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.group', verbose_name='Группа')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.subject', verbose_name='Предмет')),
            ],
            options={
                'verbose_name': 'Предмет группы',
                'verbose_name_plural': 'Предметы групп',
                'unique_together': {('subject', 'group', 'is_lecture')},
            },
        ),
        migrations.AddField(
            model_name='subject',
            name='groups',
            field=models.ManyToManyField(related_name='subjects', through='performance.SubjectGroup', to='performance.group', verbose_name='Группы'),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_number', models.CharField(blank=True, max_length=50, verbose_name='Номер студенческого')),
                ('student_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='performance.group', verbose_name='Группа')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Профиль пользователя',
                'verbose_name_plural': 'Профили пользователей',
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=50, verbose_name='ID студента')),
                ('date', models.DateField(verbose_name='Дата')),
                ('is_present', models.BooleanField(default=False, verbose_name='Присутствовал')),
                ('reason', models.TextField(blank=True, verbose_name='Причина отсутствия')),
                ('schedule_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='performance.schedule', verbose_name='Занятие')),
            ],
            options={
                'verbose_name': 'Посещаемость',
                'verbose_name_plural': 'Посещаемость',
                'ordering': ['-date'],
                'unique_together': {('student_id', 'schedule_item', 'date')},
            },
        ),
        migrations.CreateModel(
            name='Performance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.IntegerField()),
                ('year', models.IntegerField()),
                ('final_grade', models.DecimalField(decimal_places=2, max_digits=5)),
                ('attendance_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.student')),
            ],
            options={
                'indexes': [models.Index(fields=['student', 'semester', 'year'], name='performance_student_fc4bd2_idx')],
                'unique_together': {('student', 'course', 'semester', 'year')},
            },
        ),
    ]
