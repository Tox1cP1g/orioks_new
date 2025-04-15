from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, F, Avg
from django.shortcuts import get_object_or_404
from .models import (
    Semester, Subject, Grade, Schedule, Attendance, Student,
    StudentAssignment, Assignment, HomeworkAssignment, HomeworkSubmission
)
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
from datetime import datetime, timezone
from django.utils import timezone
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

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
    current_semester = Semester.objects.filter(is_current=True).first()
    schedule = Schedule.objects.filter(
        subject__semester=current_semester
    ).order_by('day_of_week', 'lesson_number') if current_semester else []
    
    context = {
        'schedule': schedule,
        'current_semester': current_semester,
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
def send_homework_view(request):
    # Получаем или создаем объект Student для текущего пользователя
    student, created = Student.objects.get_or_create(
        user=request.user,
        defaults={
            'student_number': f"ST{request.user.id}",  # Временный номер студента
            'group': 'Default Group',  # Временная группа
            'faculty': 'Default Faculty'  # Временный факультет
        }
    )

    # Получаем текущий семестр
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Получаем предметы текущего семестра
    subjects = Subject.objects.filter(semester=current_semester) if current_semester else []
    
    # Получаем последние отправленные задания
    submissions = HomeworkSubmission.objects.filter(student=student).order_by('-submitted_at')[:5]

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        assignment_id = request.POST.get('assignment')
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
        'submissions': submissions
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