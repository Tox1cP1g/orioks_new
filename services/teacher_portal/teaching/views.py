from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .models import (
    Teacher, Course, LearningMaterial, Assignment, 
    GradingCriteria, StudentSubmission, Grade,
    Subject, StudentAssignment, Schedule, Attendance
)
from .serializers import (
    TeacherSerializer, CourseSerializer, LearningMaterialSerializer,
    AssignmentSerializer, GradingCriteriaSerializer, StudentSubmissionSerializer,
    GradeSerializer, SubjectSerializer, ScheduleSerializer, AttendanceSerializer,
    StudentSerializer
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .permissions import IsTeacherOrAdmin

@login_required
def dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    # Получаем статистику
    courses_count = Course.objects.filter(teachers=teacher).count()
    pending_submissions_count = StudentSubmission.objects.filter(
        assignment__course__teachers=teacher,
        status='SUBMITTED'
    ).count()
    
    # Получаем задания на следующую неделю
    next_week = timezone.now() + timedelta(days=7)
    upcoming_assignments = Assignment.objects.filter(
        course__teachers=teacher,
        deadline__lte=next_week,
        deadline__gte=timezone.now()
    ).order_by('deadline')[:5]
    
    upcoming_assignments_count = upcoming_assignments.count()
    
    # Получаем последние решения
    recent_submissions = StudentSubmission.objects.filter(
        assignment__course__teachers=teacher,
        status='SUBMITTED'
    ).order_by('-submitted_at')[:10]
    
    # Получаем последние материалы
    recent_materials = LearningMaterial.objects.filter(
        course__teachers=teacher
    ).order_by('-created_at')[:5]
    
    context = {
        'courses_count': courses_count,
        'pending_submissions_count': pending_submissions_count,
        'upcoming_assignments_count': upcoming_assignments_count,
        'upcoming_assignments': upcoming_assignments,
        'recent_submissions': recent_submissions,
        'recent_materials': recent_materials,
    }
    
    return render(request, 'teaching/dashboard.html', context)

@login_required
def profile(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if request.method == 'POST':
        # Обновление профиля
        teacher.department = request.POST.get('department', teacher.department)
        teacher.position = request.POST.get('position', teacher.position)
        teacher.academic_degree = request.POST.get('academic_degree', teacher.academic_degree)
        teacher.phone = request.POST.get('phone', teacher.phone)
        teacher.office_hours = request.POST.get('office_hours', teacher.office_hours)
        teacher.save()
        
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')
    
    return render(request, 'teaching/profile.html', {'teacher': teacher})

@login_required
def courses(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = Course.objects.filter(teachers=teacher).order_by('-semester', 'name')
    return render(request, 'teaching/courses.html', {'courses': courses})

@login_required
def assignments(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    assignments = Assignment.objects.filter(
        course__teachers=teacher
    ).order_by('deadline')
    return render(request, 'teaching/assignments.html', {'assignments': assignments})

@login_required
def submissions(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    submissions = StudentSubmission.objects.filter(
        assignment__course__teachers=teacher,
        status='SUBMITTED'
    ).order_by('-submitted_at')
    return render(request, 'teaching/submissions.html', {'submissions': submissions})

@login_required
def grade_submission(request, submission_id):
    teacher = get_object_or_404(Teacher, user=request.user)
    submission = get_object_or_404(StudentSubmission, 
        id=submission_id,
        assignment__course__teachers=teacher
    )
    
    if request.method == 'POST':
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')
        
        if score and feedback:
            Grade.objects.create(
                submission=submission,
                graded_by=teacher,
                score=score,
                feedback=feedback
            )
            submission.status = 'COMPLETED'
            submission.save()
            
            messages.success(request, 'Оценка успешно выставлена')
            return redirect('submissions')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля')
    
    return render(request, 'teaching/grade_submission.html', {'submission': submission})

# ViewSets для API
class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Teacher.objects.all()
        return Teacher.objects.filter(user=self.request.user)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Course.objects.all()
        return Course.objects.filter(teachers__user=self.request.user)

    def perform_create(self, serializer):
        course = serializer.save()
        teacher = Teacher.objects.get(user=self.request.user)
        course.teachers.add(teacher)

class LearningMaterialViewSet(viewsets.ModelViewSet):
    queryset = LearningMaterial.objects.all()
    serializer_class = LearningMaterialSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return LearningMaterial.objects.all()
        return LearningMaterial.objects.filter(course__teachers__user=self.request.user)

    def perform_create(self, serializer):
        teacher = Teacher.objects.get(user=self.request.user)
        serializer.save(created_by=teacher)

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Assignment.objects.all()
        return Assignment.objects.filter(course__teachers__user=self.request.user)

    def perform_create(self, serializer):
        teacher = Teacher.objects.get(user=self.request.user)
        serializer.save(created_by=teacher)

    @action(detail=True, methods=['post'])
    def add_criteria(self, request, pk=None):
        assignment = self.get_object()
        serializer = GradingCriteriaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(assignment=assignment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentSubmissionViewSet(viewsets.ModelViewSet):
    queryset = StudentSubmission.objects.all()
    serializer_class = StudentSubmissionSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return StudentSubmission.objects.all()
        return StudentSubmission.objects.filter(assignment__course__teachers__user=self.request.user)

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Grade.objects.all()
        return Grade.objects.filter(graded_by__user=self.request.user)

    def perform_create(self, serializer):
        teacher = Teacher.objects.get(user=self.request.user)
        submission = get_object_or_404(StudentSubmission, id=self.request.data.get('submission'))
        
        # Проверяем, что преподаватель имеет доступ к этому заданию
        if not submission.assignment.course.teachers.filter(user=self.request.user).exists():
            return Response(
                {'error': 'У вас нет прав для оценки этого задания'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Обновляем статус задания
        submission.status = 'COMPLETED'
        submission.save()
        
        serializer.save(
            graded_by=teacher,
            submission=submission,
            graded_at=timezone.now()
        )

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'teaching/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = Teacher.objects.get(user=self.request.user)
        
        # Получаем курсы преподавателя
        courses = Course.objects.filter(teachers=teacher)
        context['courses'] = courses
        
        # Получаем последние задания
        recent_assignments = Assignment.objects.filter(
            course__teachers=teacher
        ).order_by('-created_at')[:5]
        context['recent_assignments'] = recent_assignments
        
        # Получаем работы, ожидающие проверки
        pending_submissions = StudentAssignment.objects.filter(
            assignment__course__teachers=teacher,
            status='submitted'
        ).order_by('submitted_at')
        context['pending_submissions'] = pending_submissions
        
        return context

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subject.objects.all()
        return Subject.objects.filter(teacher__user=self.request.user)

    def perform_create(self, serializer):
        teacher = Teacher.objects.get(user=self.request.user)
        serializer.save(teacher=teacher)

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Schedule.objects.all()
        return Schedule.objects.filter(teacher__user=self.request.user)

    def perform_create(self, serializer):
        teacher = Teacher.objects.get(user=self.request.user)
        serializer.save(teacher=teacher)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Attendance.objects.all()
        return Attendance.objects.filter(schedule_item__teacher__user=self.request.user)

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
            'attendances': AttendanceSerializer(attendances, many=True).data
        }

        return Response(data)

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(groups__name='STUDENT')
    serializer_class = StudentSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.filter(groups__name='STUDENT')
        return User.objects.filter(
            groups__name='STUDENT',
            studentassignment__assignment__course__teachers__user=self.request.user
        ).distinct()

def logout_view(request):
    logout(request)
    response = redirect('http://localhost:8002/login/')
    response.delete_cookie('token')
    return response
