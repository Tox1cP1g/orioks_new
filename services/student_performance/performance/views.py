from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, F, Avg
from django.shortcuts import get_object_or_404
from .models import Semester, Subject, Grade, Schedule, Attendance, Student, Group
from .serializers import (
    SemesterSerializer,
    SubjectSerializer,
    GradeSerializer,
    ScheduleSerializer,
    AttendanceSerializer,
    StudentSerializer,
    StudentGradesSerializer,
    StudentAttendanceSerializer
)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone

class TeacherPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'TEACHER'

class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [TeacherPermission]

class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [TeacherPermission]

    def get_queryset(self):
        return Subject.objects.filter(schedule_items__teacher=self.request.user.get_full_name()).distinct()

class GradeViewSet(viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [TeacherPermission]

    def get_queryset(self):
        return Grade.objects.filter(subject__schedule_items__teacher=self.request.user.get_full_name()).distinct()

    @action(detail=False, methods=['get'])
    def student_grades(self, request):
        student_id = request.query_params.get('student_id')
        subject_id = request.query_params.get('subject_id')
        
        if not student_id or not subject_id:
            return Response(
                {"error": "Both student_id and subject_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        grades = self.get_queryset().filter(
            student_id=student_id,
            subject_id=subject_id
        )

        if not grades.exists():
            return Response(
                {"error": "No grades found for this student in this subject"},
                status=status.HTTP_404_NOT_FOUND
            )

        total_score = grades.aggregate(total=Sum('score'))['total'] or 0
        max_score = grades.aggregate(total=Sum('max_score'))['total'] or 0
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        data = {
            'student_id': student_id,
            'subject_name': grades.first().subject.name,
            'total_score': total_score,
            'max_possible_score': max_score,
            'percentage': percentage,
            'grades': grades
        }

        serializer = StudentGradesSerializer(data)
        return Response(serializer.data)

class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [TeacherPermission]

    def get_queryset(self):
        # Получаем текущий семестр
        current_semester = Semester.objects.filter(is_current=True).first()
        if not current_semester:
            return Schedule.objects.none()

        # Получаем группу студента
        student = Student.objects.filter(user_id=self.request.user.id).first()
        if not student or not student.group:
            return Schedule.objects.none()

        # Возвращаем расписание для группы студента в текущем семестре
        return Schedule.objects.filter(
            semester=current_semester,
            group=student.group
        ).select_related('subject', 'group', 'semester')

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [TeacherPermission]

    def get_queryset(self):
        return Attendance.objects.filter(
            schedule_item__teacher=self.request.user.get_full_name()
        )

    @action(detail=False, methods=['get'])
    def student_attendance(self, request):
        student_id = request.query_params.get('student_id')
        subject_id = request.query_params.get('subject_id')
        
        if not student_id or not subject_id:
            return Response(
                {"error": "Both student_id and subject_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendances = self.get_queryset().filter(
            student_id=student_id,
            schedule_item__subject_id=subject_id
        )

        if not attendances.exists():
            return Response(
                {"error": "No attendance records found for this student in this subject"},
                status=status.HTTP_404_NOT_FOUND
            )

        total_classes = attendances.count()
        attended_classes = attendances.filter(is_present=True).count()
        attendance_percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0

        data = {
            'student_id': student_id,
            'subject_name': attendances.first().schedule_item.subject.name,
            'total_classes': total_classes,
            'attended_classes': attended_classes,
            'attendance_percentage': attendance_percentage,
            'attendances': attendances
        }

        serializer = StudentAttendanceSerializer(data)
        return Response(serializer.data)

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [TeacherPermission]

    def get_queryset(self):
        teacher_subjects = Subject.objects.filter(
            schedule_items__teacher=self.request.user.get_full_name()
        ).distinct()
        
        return Student.objects.filter(
            grade__subject__in=teacher_subjects
        ).distinct()

@login_required
def index(request):
    return render(request, 'student_performance/index.html')

@login_required
def grades(request):
    return render(request, 'student_performance/grades.html')

@login_required
def schedule(request):
    return render(request, 'student_performance/config.html')

def help(request):
    return render(request, 'student_performance/help.html')

@login_required
def dashboard(request):
    user = request.user
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Получаем предметы текущего семестра
    subjects = Subject.objects.filter(semester=current_semester) if current_semester else []
    
    # Получаем последние оценки
    latest_grades = Grade.objects.filter(
        student_id=str(user.id),
        subject__semester=current_semester
    ).select_related('subject').order_by('-date')[:5]
    
    # Получаем расписание на сегодня
    today = datetime.now().date()
    today_schedule = Schedule.objects.filter(
        subject__semester=current_semester,
        day_of_week=today.weekday() + 1
    ).select_related('subject').order_by('lesson_number') if current_semester else []
    
    # Получаем статистику посещаемости
    schedule_items = Schedule.objects.filter(subject__semester=current_semester) if current_semester else []
    attendance_records = Attendance.objects.filter(
        student_id=str(user.id),
        schedule_item__in=schedule_items
    )
    
    attendance_stats = {
        'total': attendance_records.count(),
        'missed': attendance_records.filter(is_present=False).count(),
        'percentage': (attendance_records.filter(is_present=True).count() / attendance_records.count() * 100) if attendance_records.exists() else 0
    }
    
    # Получаем статистику по оценкам
    grades_stats = {
        'average': Grade.objects.filter(
            student_id=str(user.id),
            subject__semester=current_semester
        ).aggregate(avg=Avg('score'))['avg'] or 0,
        'total': Grade.objects.filter(
            student_id=str(user.id),
            subject__semester=current_semester
        ).count(),
        'excellent': Grade.objects.filter(
            student_id=str(user.id),
            subject__semester=current_semester,
            score__gte=4.5
        ).count(),
        'good': Grade.objects.filter(
            student_id=str(user.id),
            subject__semester=current_semester,
            score__gte=3.5,
            score__lt=4.5
        ).count()
    }
    
    # Получаем уведомления (если есть)
    notifications = []  # Здесь можно добавить логику получения уведомлений
    
    context = {
        'user': user,
        'current_semester': current_semester,
        'subjects': subjects,
        'latest_grades': [{
            'subject': grade.subject.name,
            'value': grade.score,
            'date': grade.date.strftime('%d.%m.%Y')
        } for grade in latest_grades],
        'today_schedule': [{
            'time': schedule.get_lesson_number_display(),
            'subject': schedule.subject.name,
            'room': schedule.room,
            'teacher': schedule.teacher,
            'is_lecture': schedule.is_lecture
        } for schedule in today_schedule],
        'attendance_stats': attendance_stats,
        'grades_stats': grades_stats,
        'notifications': notifications,
    }
    return render(request, 'student_performance/dashboard.html', context)

@login_required
def grades_view(request):
    user = request.user
    semesters = Semester.objects.all()
    selected_semester = request.GET.get('semester')
    
    if selected_semester:
        semester = Semester.objects.get(id=selected_semester)
        grades = Grade.objects.filter(student_id=str(user.id), subject__semester=semester)
    else:
        current_semester = Semester.objects.filter(is_current=True).first()
        grades = Grade.objects.filter(student_id=str(user.id), subject__semester=current_semester) if current_semester else []
    
    # Получаем все предметы с оценками
    subjects_with_grades = []
    for subject in Subject.objects.filter(grades__student_id=str(user.id)).distinct():
        subject_grades = grades.filter(subject=subject)
        if subject_grades.exists():
            subjects_with_grades.append({
                'name': subject.name,
                'grades': [{
                    'type': grade.get_grade_type_display(),
                    'value': grade.score,
                    'date': grade.date,
                    'comment': grade.comment
                } for grade in subject_grades],
                'average_grade': subject_grades.aggregate(avg=Avg('score'))['avg']
            })
    
    # Рассчитываем статистику
    total_grades = grades.count()
    excellent_grades_count = grades.filter(score__gte=4.5).count()
    good_grades_count = grades.filter(score__gte=3.5, score__lt=4.5).count()
    low_grades_count = grades.filter(score__lt=3.5).count()
    average_grade = grades.aggregate(avg=Avg('score'))['avg'] or 0
    
    # Подготавливаем данные для графика
    chart_data = []
    chart_labels = []
    for grade in grades.order_by('date'):
        chart_data.append(float(grade.score))
        chart_labels.append(grade.date.strftime('%d.%m'))
    
    context = {
        'semesters': semesters,
        'grades': grades,
        'selected_semester': selected_semester,
        'subjects_with_grades': subjects_with_grades,
        'total_grades': total_grades,
        'excellent_grades_count': excellent_grades_count,
        'good_grades_count': good_grades_count,
        'low_grades_count': low_grades_count,
        'average_grade': average_grade,
        'chart_data': chart_data,
        'chart_labels': chart_labels,
    }
    return render(request, 'student_performance/grades.html', context)

@login_required
def schedule_view(request):
    # Получаем текущий семестр
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        return render(request, 'student_performance/config.html', {
            'error': 'Текущий семестр не найден'
        })

    # Получаем студента и его группу
    student = Student.objects.filter(user_id=request.user.id).first()
    if not student:
        return render(request, 'student_performance/config.html', {
            'error': 'Профиль студента не найден'
        })

    # Получаем все группы для выбора
    groups = Group.objects.all().order_by('name')

    # Определяем выбранную группу (по умолчанию - группа студента)
    selected_group_id = request.GET.get('group')
    if selected_group_id:
        selected_group = Group.objects.filter(id=selected_group_id).first()
    else:
        selected_group = student.group

    # Определяем текущую неделю
    week_param = request.GET.get('week')
    if week_param:
        current_week = datetime.strptime(week_param, '%Y-%m-%d').date()
    else:
        current_week = timezone.now().date()

    # Вычисляем начало и конец недели
    week_start = current_week - timedelta(days=current_week.weekday())
    week_end = week_start + timedelta(days=6)
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    # Получаем дни недели
    days = [week_start + timedelta(days=i) for i in range(7)]

    # Определяем временные слоты
    time_slots = [
        {'id': 1, 'start_time': '09:00', 'end_time': '10:30'},
        {'id': 2, 'start_time': '10:45', 'end_time': '12:15'},
        {'id': 3, 'start_time': '13:00', 'end_time': '14:30'},
        {'id': 4, 'start_time': '14:45', 'end_time': '16:15'},
        {'id': 5, 'start_time': '16:30', 'end_time': '18:00'},
        {'id': 6, 'start_time': '18:15', 'end_time': '19:45'},
    ]

    # Получаем расписание для выбранной группы
    schedule = Schedule.objects.filter(
        semester=current_semester,
        group=selected_group
    ).select_related('subject', 'group', 'semester').order_by('day_of_week', 'lesson_number')

    # Создаем словарь с расписанием по дням и временным слотам
    schedule_data = {}
    for day in days:
        schedule_data[day] = {}
        day_schedule = schedule.filter(day_of_week=day.weekday() + 1)
        for slot in time_slots:
            schedule_data[day][slot['id']] = day_schedule.filter(lesson_number=slot['id']).first()

    context = {
        'current_semester': current_semester,
        'groups': groups,
        'selected_group': selected_group,
        'current_week': current_week,
        'week_start': week_start,
        'week_end': week_end,
        'prev_week': prev_week,
        'next_week': next_week,
        'days': days,
        'time_slots': time_slots,
        'schedule_data': schedule_data,
    }

    return render(request, 'student_performance/config.html', context)

@login_required
def attendance_view(request):
    user = request.user
    current_semester = Semester.objects.filter(is_current=True).first()
    semesters = Semester.objects.all()
    selected_semester = request.GET.get('semester')
    
    if selected_semester:
        semester = Semester.objects.get(id=selected_semester)
    else:
        semester = current_semester
    
    subjects = Subject.objects.filter(semester=semester) if semester else []
    selected_subject = request.GET.get('subject')
    
    # Получаем все расписание для выбранного семестра
    schedule_items = Schedule.objects.filter(subject__semester=semester) if semester else []
    
    # Получаем посещаемость
    attendance_records = Attendance.objects.filter(
        student_id=str(user.id),
        schedule_item__in=schedule_items
    ).select_related('schedule_item__subject').order_by('-date')
    
    # Рассчитываем общую статистику
    total_lessons = attendance_records.count()
    attended_lessons = attendance_records.filter(is_present=True).count()
    missed_lessons = total_lessons - attended_lessons
    excused_absences = attendance_records.filter(is_present=False, reason__isnull=False).count()
    total_attendance = (attended_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    # Подготавливаем данные для графика
    chart_data = []
    chart_labels = []
    for record in attendance_records.order_by('date'):
        chart_data.append(100 if record.is_present else 0)
        chart_labels.append(record.date.strftime('%d.%m'))
    
    # Группируем посещаемость по предметам
    subjects_attendance = []
    for subject in subjects:
        subject_records = attendance_records.filter(schedule_item__subject=subject)
        if subject_records.exists():
            total_subject_lessons = subject_records.count()
            attended_subject_lessons = subject_records.filter(is_present=True).count()
            attendance_percentage = (attended_subject_lessons / total_subject_lessons * 100) if total_subject_lessons > 0 else 0
            
            subjects_attendance.append({
                'name': subject.name,
                'attendance_percentage': attendance_percentage,
                'records': [{
                    'date': record.date,
                    'time': record.schedule_item.get_lesson_number_display(),
                    'status': 'present' if record.is_present else ('excused' if record.reason else 'absent'),
                    'comment': record.reason
                } for record in subject_records]
            })
    
    context = {
        'subjects': subjects,
        'semesters': semesters,
        'selected_subject': selected_subject,
        'selected_semester': selected_semester,
        'total_attendance': total_attendance,
        'attended_lessons': attended_lessons,
        'total_lessons': total_lessons,
        'missed_lessons': missed_lessons,
        'excused_absences': excused_absences,
        'subjects_attendance': subjects_attendance,
        'chart_data': chart_data,
        'chart_labels': chart_labels,
    }
    return render(request, 'student_performance/attendance.html', context)

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        # Обработка обновления профиля
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        # Обработка изменения пароля
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                else:
                    messages.error(request, 'Новые пароли не совпадают')
            else:
                messages.error(request, 'Неверный текущий пароль')
        
        user.save()
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')
    
    context = {
        'user': user,
    }
    return render(request, 'student_performance/profile.html', context)

def logout_view(request):
    logout(request)
    response = redirect('http://localhost:8002/login/')
    response.delete_cookie('token')
    return response

@login_required
def add_grade_view(request):
    # Проверяем, что пользователь является преподавателем
    if not hasattr(request.user, 'role') or request.user.role != 'TEACHER':
        messages.error(request, 'Только преподаватели могут добавлять оценки')
        return redirect('grades')

    # Получаем текущий семестр
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        messages.error(request, 'Текущий семестр не найден')
        return redirect('grades')

    # Получаем предметы, которые ведет преподаватель
    teacher_subjects = Subject.objects.filter(
        schedule_items__teacher=request.user.get_full_name(),
        semester=current_semester
    ).distinct()

    # Получаем студентов, которые учатся у преподавателя
    students = Student.objects.filter(
        group__subjects__in=teacher_subjects
    ).select_related('user', 'group').distinct()

    if request.method == 'POST':
        try:
            student = Student.objects.get(id=request.POST.get('student'))
            subject = Subject.objects.get(id=request.POST.get('subject'))
            
            # Проверяем, что преподаватель может ставить оценки по этому предмету
            if not subject.schedule_items.filter(teacher=request.user.get_full_name()).exists():
                messages.error(request, 'У вас нет прав для выставления оценок по этому предмету')
                return redirect('add_grade')

            grade = Grade.objects.create(
                student=student,
                subject=subject,
                grade_type=request.POST.get('grade_type'),
                score=float(request.POST.get('score')),
                max_score=float(request.POST.get('max_score')),
                date=request.POST.get('date'),
                comment=request.POST.get('comment')
            )
            messages.success(request, 'Оценка успешно добавлена')
            return redirect('grades')
        except (Student.DoesNotExist, Subject.DoesNotExist) as e:
            messages.error(request, 'Ошибка при добавлении оценки: ' + str(e))
        except Exception as e:
            messages.error(request, 'Произошла ошибка при добавлении оценки')

    # Получаем типы оценок из модели Grade
    grade_types = Grade.GRADE_TYPE_CHOICES

    context = {
        'students': students,
        'subjects': teacher_subjects,
        'grade_types': grade_types,
    }
    return render(request, 'student_performance/add_grade.html', context) 