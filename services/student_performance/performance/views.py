from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, F
from django.shortcuts import get_object_or_404
from .models import Semester, Subject, Grade, Schedule, Attendance, Student
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
    subjects = Subject.objects.filter(semester=current_semester) if current_semester else []
    recent_grades = Grade.objects.filter(student_id=user.id).order_by('-date')[:5]
    
    context = {
        'current_semester': current_semester,
        'subjects': subjects,
        'recent_grades': recent_grades,
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
    
    context = {
        'semesters': semesters,
        'grades': grades,
        'selected_semester': selected_semester,
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
    subjects = Subject.objects.filter(semester=current_semester) if current_semester else []
    
    selected_subject = request.GET.get('subject')
    if selected_subject:
        # Получаем все расписание для выбранного предмета
        schedule_items = Schedule.objects.filter(subject_id=selected_subject)
        
        # Получаем посещаемость для всех занятий этого предмета
        attendance = Attendance.objects.filter(
            student_id=str(user.id),  # Преобразуем ID в строку
            schedule_item__in=schedule_items
        ).select_related('schedule_item__subject').order_by('-date')
    else:
        attendance = []
    
    context = {
        'subjects': subjects,
        'attendance': attendance,
        'selected_subject': selected_subject,
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