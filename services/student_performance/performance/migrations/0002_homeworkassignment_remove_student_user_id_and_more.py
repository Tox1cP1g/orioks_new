# Generated by Django 4.2.20 on 2025-03-19 12:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('performance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomeworkAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('deadline', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('max_points', models.DecimalField(decimal_places=2, default=100.0, max_digits=5)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='homework_assignments', to='performance.subject')),
            ],
        ),
        migrations.RemoveField(
            model_name='student',
            name='user_id',
        ),
        migrations.AddField(
            model_name='student',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='submission_file',
            field=models.FileField(blank=True, null=True, upload_to='submissions/', verbose_name='Файл с решением'),
        ),
        migrations.CreateModel(
            name='HomeworkSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to='homework_submissions/')),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('SUBMITTED', 'Отправлено'), ('CHECKING', 'На проверке'), ('GRADED', 'Оценено'), ('REJECTED', 'Отклонено')], default='SUBMITTED', max_length=20)),
                ('grade', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('feedback', models.TextField(blank=True)),
                ('checked_at', models.DateTimeField(blank=True, null=True)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='performance.homeworkassignment')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='homework_submissions', to='performance.student')),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
    ]
