from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, F, Avg
from django.shortcuts import get_object_or_404
from .models import (
    Semester, Subject, Grade, Schedule, Attendance, Student,
    StudentAssignment, Assignment, HomeworkAssignment, HomeworkSubmission, Group, Teacher, SubjectTeacher
)
from .serializers import (
    SemesterSerializer,
    SubjectSerializer,
    GradeSerializer,
    ScheduleSerializer,
    AttendanceSerializer,
    StudentSerializer,
    StudentGradesSerializer,
    StudentAttendanceSerializer,
    TeacherSerializer,
    SubjectTeacherSerializer
)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.db import models
from datetime import datetime, timezone, timedelta
from django.utils import timezone
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.conf import settings
from django.db.models import Q
import json

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
        return Schedule.objects.filter(teacher=self.request.user.get_full_name())

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
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.method == 'POST':
        try:
            # Получаем или создаем запись о задании студента
            student_assignment, created = StudentAssignment.objects.get_or_create(
                student=request.user,
                assignment=assignment,
                defaults={'status': 'SUBMITTED'}
            )
            
            # Обновляем данные
            student_assignment.submission_text = request.POST.get('submission_text', '')
            student_assignment.submitted_at = timezone.now()
            student_assignment.status = 'SUBMITTED'
            
            # Обрабатываем загруженный файл
            if 'file' in request.FILES:
                student_assignment.submission_file = request.FILES['file']
            
            student_assignment.save()
            
            messages.success(request, 'Задание успешно отправлено!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Ошибка при отправке задания: {str(e)}')
    
    return render(request, 'student_performance/send_homework.html', {
        'assignment': assignment
    })

@login_required
def index(request):
    return render(request, 'student_performance/index.html')

@login_required
def grades(request):
    return render(request, 'student_performance/grades.html')

@login_required
def schedule(request):
    return render(request, 'student_performance/schedule.html')

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
            'room': schedule.room
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
    from datetime import datetime, timedelta
    
    # Получаем текущий семестр
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Определяем текущую дату и начало/конец недели
    current_date = timezone.now().date()
    
    # Получаем параметр week из запроса, если он есть
    week_param = request.GET.get('week')
    if week_param:
        try:
            # Если указана дата, начинаем с нее
            current_date = datetime.strptime(week_param, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Вычисляем начало недели (понедельник)
    start_of_week = current_date - timedelta(days=current_date.weekday())
    # Вычисляем конец недели (воскресенье)
    end_of_week = start_of_week + timedelta(days=6)
    
    # Даты для навигации между неделями
    prev_week = start_of_week - timedelta(days=7)
    next_week = start_of_week + timedelta(days=7)
    
    # Создаем список дней недели
    days = [start_of_week + timedelta(days=i) for i in range(7)]
    
    # Получаем все группы
    groups = Group.objects.all()
    selected_group_id = request.GET.get('group')
    selected_group = None
    
    if selected_group_id:
        try:
            selected_group = Group.objects.get(id=selected_group_id)
        except Group.DoesNotExist:
            pass
    else:
        # Если группа не выбрана, пытаемся определить группу студента
        student = Student.objects.filter(user_id=request.user.id).first()
        if student and student.group:
            selected_group = student.group
        elif groups.exists():
            selected_group = groups.first()
    
    # Получаем расписание для выбранной группы и семестра
    schedule_items = []
    if current_semester and selected_group:
        schedule_items = Schedule.objects.filter(
            semester=current_semester,
            group=selected_group.name
        ).order_by('day_of_week', 'lesson_number')
    
    # Создаем временные слоты для расписания
    time_slots = [
        {'slot': 1, 'start_time': '9:00-10:30'},
        {'slot': 2, 'start_time': '10:45-12:15'},
        {'slot': 3, 'start_time': '13:00-14:30'},
        {'slot': 4, 'start_time': '14:45-16:15'},
        {'slot': 5, 'start_time': '16:30-18:00'},
        {'slot': 6, 'start_time': '18:15-19:45'}
    ]
    
    # Подготавливаем данные расписания в формате, удобном для шаблона
    schedule_data = []
    for slot in time_slots:
        slot_data = {'time': slot['start_time'], 'days': []}
        
        for day_idx, day in enumerate(days, 1):
            day_lessons = []
            
            # Находим занятия для текущего дня и временного слота
            for item in schedule_items:
                if item.day_of_week == day_idx and item.lesson_number == slot['slot']:
                    day_lessons.append({
                        'subject': item.subject.name,
                        'room': item.room,
                        'teacher': item.teacher,
                        'is_lecture': item.is_lecture
                    })
            
            slot_data['days'].append({
                'date': day,
                'lessons': day_lessons
            })
        
        schedule_data.append(slot_data)
    
    context = {
        'schedule_data': schedule_data,
        'time_slots': time_slots,
        'days': days,
        'today': current_date,
        'week_start': start_of_week,
        'week_end': end_of_week,
        'prev_week': prev_week,
        'next_week': next_week,
        'current_week': current_date,
        'week_param': week_param,
        'current_semester': current_semester,
        'groups': groups,
        'selected_group': selected_group,
    }
    
    return render(request, 'student_performance/schedule.html', context)

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
@ensure_csrf_cookie
@csrf_protect
def send_homework_view(request, assignment_id=None):
    # Получаем или создаем объект Student для текущего пользователя
    student, created = Student.objects.get_or_create(
        user_id=request.user.id,
        defaults={
            'student_number': f"ST{request.user.id}",  # Временный номер студента
            'faculty': 'Default Faculty'  # Временный факультет
        }
    )

    # Получаем текущий семестр
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Получаем предметы текущего семестра
    subjects = Subject.objects.filter(semester=current_semester) if current_semester else []
    
    # Получаем последние отправленные задания
    submissions = HomeworkSubmission.objects.filter(student=student).order_by('-submitted_at')[:5]

    # Если указан ID задания, попробуем его найти
    selected_assignment = None
    if assignment_id:
        selected_assignment = HomeworkAssignment.objects.filter(id=assignment_id).first()

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        assignment_id = request.POST.get('assignment') or assignment_id
        description = request.POST.get('description')
        file = request.FILES.get('file')

        if not all([subject_id, assignment_id, file]):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return redirect('send_homework')

        try:
            # Получаем предмет
            subject = Subject.objects.get(id=subject_id)
            
            # Создаем или получаем задание
            assignment, created = HomeworkAssignment.objects.get_or_create(
                id=assignment_id,
                defaults={
                    'subject': subject,
                    'name': dict(
                        [(1, 'БДЗ'),
                         (2, 'Лабораторная работа'),
                         (3, 'Курсовая работа'),
                         (4, 'Отработка')]
                    ).get(int(assignment_id), 'Неизвестное задание'),
                    'description': 'Автоматически созданное задание',
                    'deadline': timezone.now() + timezone.timedelta(days=14)
                }
            )

            # Создаем новую отправку
            submission = HomeworkSubmission.objects.create(
                student=student,
                assignment=assignment,
                description=description,
                file=file,
                status='SUBMITTED'
            )

            messages.success(request, 'Задание успешно отправлено')
            return redirect('send_homework')

        except Subject.DoesNotExist:
            messages.error(request, 'Выбранный предмет не найден')
            return redirect('send_homework')
        except Exception as e:
            messages.error(request, f'Произошла ошибка: {str(e)}')
            return redirect('send_homework')

    return render(request, 'student_performance/send_homework.html', {
        'subjects': subjects,
        'submissions': submissions,
        'selected_assignment': selected_assignment
    })

@login_required
@ensure_csrf_cookie
@csrf_protect
def get_assignments_api(request, subject_id):
    try:
        # Статический список заданий
        static_assignments = [
            {
                'id': 1,
                'name': 'БДЗ',
                'description': 'Большое домашнее задание',
                'deadline': (timezone.now() + timezone.timedelta(days=14)).isoformat()
            },
            {
                'id': 2,
                'name': 'Лабораторная работа',
                'description': 'Лабораторная работа по предмету',
                'deadline': (timezone.now() + timezone.timedelta(days=7)).isoformat()
            },
            {
                'id': 3,
                'name': 'Курсовая работа',
                'description': 'Курсовая работа по предмету',
                'deadline': (timezone.now() + timezone.timedelta(days=30)).isoformat()
            },
            {
                'id': 4,
                'name': 'Отработка',
                'description': 'Отработка пропущенных занятий',
                'deadline': (timezone.now() + timezone.timedelta(days=5)).isoformat()
            }
        ]
        
        return JsonResponse(static_assignments, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@ensure_csrf_cookie
@csrf_protect
def add_grade_view(request):
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            subject_id = request.POST.get('subject_id')
            grade_value = request.POST.get('grade')
            semester_id = request.POST.get('semester_id')
            
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            semester = get_object_or_404(Semester, id=semester_id)
            
            grade = Grade.objects.create(
                student=student,
                subject=subject,
                grade=grade_value,
                semester=semester,
                teacher=request.user.get_full_name()
            )
            
            messages.success(request, 'Оценка успешно добавлена')
            return redirect('grades')
            
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении оценки: {str(e)}')
            return redirect('grades')
    
    # Если метод GET, показываем форму
    students = Student.objects.all()
    subjects = Subject.objects.all()
    semesters = Semester.objects.all()
    
    return render(request, 'performance/add_grade.html', {
        'students': students,
        'subjects': subjects,
        'semesters': semesters
    })

@login_required
def subjects(request):
    user = request.user
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Получаем предметы текущего семестра
    subjects = Subject.objects.filter(semester=current_semester) if current_semester else []
    
    # Получаем статистику по каждому предмету
    subjects_data = []
    for subject in subjects:
        grades = Grade.objects.filter(
            student_id=str(user.id),
            subject=subject
        )
        attendance = Attendance.objects.filter(
            student_id=str(user.id),
            schedule_item__subject=subject
        )
        
        subjects_data.append({
            'subject': subject,
            'average_grade': grades.aggregate(avg=Avg('score'))['avg'] or 0,
            'attendance_percentage': (attendance.filter(is_present=True).count() / attendance.count() * 100) if attendance.exists() else 0,
            'total_assignments': HomeworkAssignment.objects.filter(subject=subject).count(),
            'completed_assignments': HomeworkSubmission.objects.filter(
                student__user_id=user.id,
                assignment__subject=subject,
                status='SUBMITTED'
            ).count()
        })
    
    return render(request, 'student_performance/subjects.html', {
        'subjects_data': subjects_data,
        'current_semester': current_semester
    })

@login_required
def assignments(request):
    user = request.user
    current_semester = Semester.objects.filter(is_current=True).first()
    subject_id = request.GET.get('subject')
    
    # Получаем предметы текущего семестра
    subjects = Subject.objects.filter(semester=current_semester) if current_semester else []
    
    # Если выбран конкретный предмет, фильтруем задания
    if subject_id:
        assignments = HomeworkAssignment.objects.filter(
            subject_id=subject_id,
            subject__semester=current_semester
        ).order_by('-deadline')
        selected_subject = Subject.objects.get(id=subject_id)
    else:
        assignments = HomeworkAssignment.objects.filter(
            subject__semester=current_semester
        ).order_by('-deadline')
        selected_subject = None
    
    # Получаем статус выполнения для каждого задания
    assignments_data = []
    for assignment in assignments:
        # Получаем статус студента через HomeworkSubmission
        student = Student.objects.filter(user_id=user.id).first()
        homework_submission = HomeworkSubmission.objects.filter(
            student=student,
            assignment=assignment
        ).first() if student else None
        
        assignments_data.append({
            'assignment': assignment,
            'status': homework_submission.status if homework_submission else 'NOT_STARTED',
            'submitted_at': homework_submission.submitted_at if homework_submission else None,
            'grade': homework_submission.grade if homework_submission else None
        })
    
    return render(request, 'student_performance/assignments.html', {
        'assignments_data': assignments_data,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'current_semester': current_semester
    })

@login_required
def news(request):
    # Получаем полный URL запроса
    full_url = request.build_absolute_uri()
    print(f"Full URL: {full_url}")  # Логируем полный URL
    
    # Получаем параметр source из URL
    source = request.GET.get('source', '')
    print(f"Source parameter: {source}")  # Логируем параметр source
    
    # Определяем порт и роль на основе параметра source
    if source == 'teacher':
        source_port = '8004'
        role = 'TEACHER'
    else:
        source_port = '8003'
        role = 'STUDENT'
    
    print(f"Source port: {source_port}")  # Логируем определенный порт
    print(f"Role: {role}")  # Логируем роль
    
    # Формируем URL для перенаправления на сервис новостей (8007)
    redirect_url = f'http://localhost:8007/?source_port={source_port}&role={role}'
    print(f"Redirect URL: {redirect_url}")  # Логируем URL для перенаправления
    
    return redirect(redirect_url)

class TeacherViewSet(viewsets.ModelViewSet):
    """API для преподавателей"""
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Возможность фильтрации по полям"""
        queryset = Teacher.objects.all()
        
        # Фильтрация по кафедре
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)
            
        # Фильтрация по ФИО
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                Q(first_name__icontains=name) | 
                Q(last_name__icontains=name) | 
                Q(middle_name__icontains=name)
            )
            
        return queryset

class SubjectTeacherViewSet(viewsets.ModelViewSet):
    """API для связей преподавателей с предметами"""
    queryset = SubjectTeacher.objects.all()
    serializer_class = SubjectTeacherSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Возможность фильтрации по полям"""
        queryset = SubjectTeacher.objects.all()
        
        # Фильтрация по ID предмета
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
            
        # Фильтрация по ID преподавателя
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
            
        # Фильтрация по роли преподавателя
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role__icontains=role)
            
        # Фильтрация основных преподавателей
        is_main = self.request.query_params.get('is_main')
        if is_main is not None:
            is_main_bool = is_main.lower() == 'true'
            queryset = queryset.filter(is_main=is_main_bool)
            
        return queryset 

@login_required
def live_subject_teachers(request):
    """
    Получает данные о преподавателях и предметах напрямую с портала преподавателя
    через API-запрос в реальном времени
    """
    # Пробуем новые URL, которые должны гарантированно возвращать JSON
    urls = [
        'http://localhost:8004/api/raw-json-api/teachers/',
        'http://localhost:8004/raw-json-api/teachers/',
        'http://localhost:8004/api/v1/public/data.json',
        'http://localhost:8004/public-teacher-subjects.json',
        'http://localhost:8004/api/public/teachers/',
        'http://localhost:8004/public-teacher-subjects/'
    ]
    debug_info = []
    
    try:
        # Проходим по списку URL и используем первый успешный
        response = None
        used_url = None
        
        for url in urls:
            debug_info.append(f"Пробуем запрос к API: {url}")
            try:
                # Явно указываем, что ожидаем JSON в заголовке Accept
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest' # Добавляем AJAX-заголовок
                }
                curr_response = requests.get(url, headers=headers, timeout=5)
                debug_info.append(f"Ответ: статус {curr_response.status_code}")
                
                # Проверяем, что получили JSON
                if curr_response.status_code == 200 and curr_response.text.strip():
                    # Пытаемся прочитать как JSON
                    try:
                        json.loads(curr_response.text)
                        # Если дошли до этой строки, значит ответ валидный JSON
                        response = curr_response
                        used_url = url
                        debug_info.append(f"Получен валидный JSON ответ")
                        break
                    except json.JSONDecodeError as e:
                        debug_info.append(f"Ответ не является валидным JSON: {e}")
                        debug_info.append(f"Первые 100 символов ответа: {curr_response.text[:100]}...")
            except requests.RequestException as e:
                debug_info.append(f"Ошибка запроса к {url}: {str(e)}")
        
        # Если ни один URL не сработал, используем тестовые данные
        if response is None:
            debug_info.append("Все API-запросы не удались, используем тестовые данные")
            data = create_test_data_for_views()
        else:
            debug_info.append(f"Успешный ответ от {used_url}")
            try:
                data = response.json()
                debug_info.append(f"JSON успешно разобран, получено {len(data)} элементов")
            except json.JSONDecodeError as json_err:
                # На этот раз такой ошибки быть не должно, т.к. мы уже проверили JSON
                error_msg = f"Неожиданная ошибка декодирования JSON: {json_err}"
                debug_info.append(error_msg)
                print(error_msg)
                print(f"Полученный текст: {response.text[:100]}")
                debug_info.append(f"Текст ответа: {response.text[:100]}")
                # Используем тестовые данные
                data = create_test_data_for_views()
                debug_info.append("Используем тестовые данные")
        
        # Группируем преподавателей по предметам для удобного отображения
        subjects_dict = {}
        
        for item in data:
            # Проверяем структуру данных - она может быть разной в зависимости от API
            if 'subject' in item:
                # Вложенная структура
                subject_data = item.get('subject', {})
                subject_id = subject_data.get('id')
                subject_name = subject_data.get('name', '')
                subject_semester = subject_data.get('semester', '')
                subject_description = subject_data.get('description', '')
                
                teacher_data = item.get('teacher', {})
                teacher_id = teacher_data.get('id')
                teacher_name = teacher_data.get('name', '')
                teacher_position = teacher_data.get('position', '')
                teacher_department = teacher_data.get('department', '')
                teacher_academic_degree = teacher_data.get('academic_degree', '')
                
                role = item.get('role_display', item.get('role', ''))
                is_main = item.get('is_main', False)
            else:
                # Плоская структура
                subject_id = item.get('subject_id')
                subject_name = item.get('subject_name', '')
                subject_semester = ''  # Может отсутствовать в плоской структуре
                subject_description = ''  # Может отсутствовать в плоской структуре
                
                teacher_id = item.get('teacher_id')
                teacher_name = item.get('teacher_full_name', '')
                teacher_position = ''  # Может отсутствовать в плоской структуре
                teacher_department = ''  # Может отсутствовать в плоской структуре
                teacher_academic_degree = ''  # Может отсутствовать в плоской структуре
                
                role = item.get('role', '')
                is_main = item.get('is_main', False)
            
            if subject_id not in subjects_dict:
                subjects_dict[subject_id] = {
                    'id': subject_id,
                    'name': subject_name,
                    'semester': subject_semester,
                    'description': subject_description,
                    'teachers': []
                }
            
            # Добавляем информацию о преподавателе для этого предмета
            teacher_info = {
                'id': teacher_id,
                'name': teacher_name,
                'position': teacher_position,
                'department': teacher_department,
                'academic_degree': teacher_academic_degree,
                'role': role,
                'is_main': is_main
            }
            
            subjects_dict[subject_id]['teachers'].append(teacher_info)
        
        # Преобразуем словарь в список для передачи в шаблон
        subjects_list = list(subjects_dict.values())
        debug_info.append(f"Подготовлены данные для {len(subjects_list)} предметов")
        
        context = {
            'subjects': subjects_list,
            'error': None,
            'debug_info': debug_info,
        }
        
    except requests.RequestException as e:
        error_msg = f'Ошибка при обращении к порталу преподавателя: {str(e)}'
        debug_info.append(error_msg)
        context = {
            'subjects': [],
            'error': error_msg,
            'debug_info': debug_info,
        }
    except json.JSONDecodeError as json_err:
        error_msg = f'Ошибка при обработке ответа от портала преподавателя: {str(json_err)}'
        debug_info.append(error_msg)
        print(f"Общая ошибка декодирования JSON: {json_err}")
        context = {
            'subjects': [],
            'error': error_msg,
            'debug_info': debug_info,
        }
    
    return render(request, 'performance/live_subject_teachers.html', context)

def create_test_data_for_views():
    """Создает тестовые данные о связях преподавателей с предметами для отображения"""
    from .models import Subject
    
    # Получаем реальные предметы из БД
    subjects = Subject.objects.all()
    
    # Создаем тестовые связи для предметов
    test_relations = []
    test_teachers = [
        {
            'id': 1001,
            'name': 'Иванов Иван Иванович',
            'position': 'Доцент',
            'department': 'Кафедра информационных технологий',
            'academic_degree': 'к.т.н.'
        },
        {
            'id': 1002,
            'name': 'Петров Петр Петрович',
            'position': 'Профессор',
            'department': 'Кафедра информационных технологий',
            'academic_degree': 'д.т.н.'
        },
        {
            'id': 1003,
            'name': 'Сидорова Анна Алексеевна',
            'position': 'Старший преподаватель',
            'department': 'Кафедра математики',
            'academic_degree': 'к.ф-м.н.'
        }
    ]
    
    for idx, subject in enumerate(subjects):
        # Основной преподаватель
        main_teacher = test_teachers[idx % len(test_teachers)]
        test_relations.append({
            'subject': {
                'id': subject.id,
                'name': subject.name,
                'semester': getattr(subject.semester, 'name', 'Неизвестный семестр'),
                'description': subject.description
            },
            'teacher': main_teacher,
            'role': 'Лектор',
            'role_display': 'Лектор',
            'is_main': True
        })
        
        # Дополнительный преподаватель
        second_teacher = test_teachers[(idx + 1) % len(test_teachers)]
        test_relations.append({
            'subject': {
                'id': subject.id,
                'name': subject.name,
                'semester': getattr(subject.semester, 'name', 'Неизвестный семестр'),
                'description': subject.description
            },
            'teacher': second_teacher,
            'role': 'Руководитель практики',
            'role_display': 'Руководитель практики',
            'is_main': False
        })
    
    return test_relations 