from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from rest_framework import viewsets, status, views
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .models import (
    Teacher, Course, LearningMaterial, Assignment, 
    GradingCriteria, StudentSubmission, Grade,
    Subject, StudentAssignment, Schedule, Attendance,
    SubjectTeacher, SubjectTeacherGroup
)
from .serializers import (
    TeacherSerializer, CourseSerializer, LearningMaterialSerializer,
    AssignmentSerializer, GradingCriteriaSerializer, StudentSubmissionSerializer,
    GradeSerializer, SubjectSerializer, ScheduleSerializer, AttendanceSerializer,
    StudentSerializer, SubjectTeacherSerializer
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .permissions import IsTeacherOrAdmin
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django import forms
from django.contrib.auth.models import Group

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
    """
    Представление для профиля пользователя
    """
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
    """
    Представление для страницы курсов
    """
    return render(request, 'teaching/courses.html')

@login_required
def create_course(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        semester = request.POST.get('semester')
        teachers = request.POST.getlist('teachers')  # Получаем список преподавателей

        # Создаем новый курс
        if name and description and semester and teachers:
            course = Course.objects.create(
                name=name,
                description=description,
                semester=semester
            )
            # Добавляем преподавателей в курс
            for teacher_id in teachers:
                teacher = Teacher.objects.get(id=teacher_id)
                course.teachers.add(teacher)

            course.save()
            messages.success(request, 'Курс успешно создан!')
            return redirect('courses')  # Перенаправление на страницу курсов
        else:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')

    # Получаем список всех преподавателей для отображения в форме
    teachers = Teacher.objects.all()
    return render(request, 'teaching/create_course.html', {'teachers': teachers})

@login_required
def assignments(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    assignments = Assignment.objects.filter(
        course__teachers=teacher
    ).order_by('deadline')
    return render(request, 'teaching/assignments.html', {'assignments': assignments})

@login_required
def create_assignment(request):
    """Создание нового задания"""
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = Course.objects.filter(teachers=teacher)
    assignment_types = Assignment.ASSIGNMENT_TYPES

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        course_id = request.POST.get("course")
        assignment_type = request.POST.get("type")
        max_score = request.POST.get("max_score")
        deadline = request.POST.get("deadline")

        # Проверяем, существует ли курс
        course = get_object_or_404(Course, id=course_id)


        if max_score:
            try:
                max_score = Decimal(max_score)
            except (InvalidOperation, ValueError, TypeError):
                messages.error(request, "Ошибка: Максимальный балл должен быть числом.")
                return render(request, "teaching/assignment_form.html", {
                    "courses": courses,
                    "assignment_types": assignment_types,
                    "title": title,
                    "description": description,
                    "selected_course": course_id,
                    "selected_type": assignment_type,
                    "max_score": max_score,
                    "deadline": deadline
                })
        else:
            max_score = None


        Assignment.objects.create(
            course=course,
            created_by=teacher,
            title=title,
            description=description,
            type=assignment_type,
            max_score=max_score,
            deadline=deadline
        )

        messages.success(request, "Задание успешно создано!")
        return redirect("assignments_list")

    return render(request, "teaching/assignment_form.html", {
        "courses": courses,
        "assignment_types": assignment_types
    })

@login_required
def submissions(request):
    """
    Представление для страницы проверки работ
    """
    return render(request, 'teaching/submissions.html')

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
    """API для управления преподавателями"""
    queryset = Teacher.objects.all().order_by('id')
    serializer_class = TeacherSerializer
    
    def get_permissions(self):
        """Определение прав доступа в зависимости от действия"""
        if self.action == 'list' or self.action == 'retrieve':
            # Для просмотра списка и деталей доступно всем аутентифицированным пользователям
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Для изменения данных требуются права преподавателя или админа
            permission_classes = [IsTeacherOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Фильтрация преподавателей"""
        queryset = Teacher.objects.all().order_by('id')
        
        # Фильтр по кафедре
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        # Фильтр по должности
        position = self.request.query_params.get('position')
        if position:
            queryset = queryset.filter(position__icontains=position)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        """Получить все предметы для преподавателя"""
        teacher = self.get_object()
        # Получаем предметы через связи
        subject_teachers = SubjectTeacher.objects.filter(teacher=teacher)
        subjects = [st.subject for st in subject_teachers]
        return Response(SubjectSerializer(subjects, many=True).data)

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
    queryset = Subject.objects.all().order_by('id')
    serializer_class = SubjectSerializer

    def get_permissions(self):
        """Определение прав доступа в зависимости от действия"""
        if self.action == 'list' or self.action == 'retrieve':
            # Для просмотра списка и деталей доступно всем аутентифицированным пользователям
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Для изменения данных требуются права преподавателя или админа
            permission_classes = [IsTeacherOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = Subject.objects.all().order_by('id')
        # Если пользователь имеет ограниченные права, фильтруем предметы
        if not self.request.user.is_staff and not self.action == 'list':
            return queryset.filter(teacher__user=self.request.user)
        return queryset

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
    """
    Представление для выхода из системы
    """
    logout(request)
    return redirect('index')

@login_required
def homework(request):
    return render(request, 'teaching/homework.html')

@login_required
def subject_teachers(request):
    """
    Представление для страницы связей преподаватель-предмет
    """
    teacher = get_object_or_404(Teacher, user=request.user)
    subjects = Subject.objects.all()
    teachers = Teacher.objects.all()
    subject_teachers = SubjectTeacher.objects.all().prefetch_related('groups')
    
    # Получаем все доступные группы
    groups = Group.objects.all()

    return render(request, 'teaching/subject_teachers.html', {
        'teacher': teacher,
        'subjects': subjects,
        'teachers': teachers,
        'subject_teachers': subject_teachers,
        'groups': groups
    })

@login_required
def subject_teacher_create(request):
    """
    Представление для создания связи предмет-преподаватель
    """
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        groups_names = request.POST.getlist('groups', [])  # Имена/коды групп
        
        # Отладочная информация
        print("="*50)
        print("ФОРМА ОТПРАВЛЕНА:")
        print(f"Метод: {request.method}")
        print(f"subject_id: {subject_id}")
        print(f"groups_names: {groups_names}")
        print(f"Все поля: {request.POST}")
        print(f"AJAX запрос: {'X-Requested-With' in request.headers}")
        print("="*50)
        
        success = False
        error_message = ""
        
        if subject_id:  # Проверяем только наличие subject_id
            try:
                subject = Subject.objects.get(pk=subject_id)
                current_teacher = Teacher.objects.get(user=request.user)
                
                # Создаем связь между текущим преподавателем и предметом
                subject_teacher = SubjectTeacher.objects.create(
                    subject=subject,
                    teacher=current_teacher,
                    role='LECTURER',  # Роль по умолчанию
                    is_main=True     # Первый преподаватель считается основным
                )
                
                # Сохраняем связь с группами, если они выбраны
                if groups_names:
                    for group_name in groups_names:
                        try:
                            # Получаем или создаем группу
                            group, created = Group.objects.get_or_create(name=group_name)
                            if created:
                                print(f"Создана новая группа: {group.name}")
                            
                            # Добавляем группу к связи преподаватель-предмет
                            subject_teacher.groups.add(group)
                            print(f"Добавлена группа {group.name} для связи {subject_teacher}")
                        except Exception as e:
                            print(f"Ошибка при добавлении группы {group_name}: {str(e)}")
                    
                    groups_str = ", ".join(groups_names)
                    print(f"Для связи {subject_teacher} выбраны группы: {groups_str}")
                else:
                    print(f"Для связи {subject_teacher} группы не выбраны")
                
                success = True
                messages.success(request, f'Связь с предметом "{subject.name}" успешно создана')
            except Subject.DoesNotExist:
                error_message = 'Ошибка при создании связи: предмет не найден'
                messages.error(request, error_message)
                print(f"Ошибка: предмет с ID {subject_id} не найден")
            except Exception as e:
                error_message = f'Произошла ошибка: {str(e)}'
                messages.error(request, error_message)
                print(f"Произошла ошибка: {str(e)}")
                print(f"Тип ошибки: {type(e)}")
                import traceback
                traceback.print_exc()
        else:
            error_message = 'Пожалуйста, выберите предмет'
            messages.error(request, error_message)
            print("Ошибка: не выбран предмет")
        
        # Если это AJAX запрос, возвращаем JSON ответ
        if 'X-Requested-With' in request.headers and request.headers['X-Requested-With'] == 'XMLHttpRequest':
            if success:
                return JsonResponse({'success': True, 'message': 'Предмет успешно добавлен'})
            else:
                return JsonResponse({'success': False, 'message': error_message}, status=400)
    else:
        print("Запрос к subject_teacher_create не методом POST", request.method)
            
    return redirect('subject_teachers')

@login_required
def subject_teacher_delete(request, subject_teacher_id):
    """
    Представление для удаления связи преподаватель-предмет
    """
    subject_teacher = get_object_or_404(SubjectTeacher, pk=subject_teacher_id)
    
    if request.method == 'POST':
        subject_name = subject_teacher.subject.name
        teacher_name = subject_teacher.teacher.user.get_full_name()
        
        subject_teacher.delete()
        messages.success(request, f'Связь между преподавателем {teacher_name} и предметом {subject_name} успешно удалена')
        
    return redirect('subject_teachers')

class SubjectTeacherViewSet(viewsets.ModelViewSet):
    """API для управления связями преподавателей с предметами"""
    queryset = SubjectTeacher.objects.all().order_by('id')
    serializer_class = SubjectTeacherSerializer
    
    def get_permissions(self):
        """Определение прав доступа в зависимости от действия"""
        if self.action == 'list' or self.action == 'retrieve':
            # Для просмотра списка и деталей доступно всем аутентифицированным пользователям
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Для изменения данных требуются права преподавателя или админа
            permission_classes = [IsTeacherOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Фильтрация связей"""
        queryset = SubjectTeacher.objects.all().order_by('id')
        
        # Фильтр по предмету
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
            
        # Фильтр по преподавателю
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
            
        # Фильтр по роли
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        # Фильтр по основному преподавателю
        is_main = self.request.query_params.get('is_main')
        if is_main is not None:
            is_main_bool = is_main.lower() == 'true'
            queryset = queryset.filter(is_main=is_main_bool)
            
        return queryset
    
    def perform_create(self, serializer):
        """При создании связи, если не указан teacher, использовать текущего пользователя"""
        if not self.request.data.get('teacher_id') and not self.request.user.is_staff:
            try:
                teacher = Teacher.objects.get(user=self.request.user)
                serializer.save(teacher=teacher)
            except Teacher.DoesNotExist:
                raise serializers.ValidationError("Текущий пользователь не является преподавателем")
        else:
            serializer.save()

    @action(detail=False, methods=['get'], url_path='for-student-portal', permission_classes=[permissions.AllowAny])
    def for_student_portal(self, request):
        """API для интеграции с порталом студента - получение связей преподаватель-предмет"""
        # Получаем все активные связи (можно добавить дополнительную фильтрацию)
        teacher_subjects = SubjectTeacher.objects.all().order_by('id')
        
        # Формируем данные в удобном для студенческого портала формате
        result = []
        
        for ts in teacher_subjects:
            teacher_data = {
                'id': ts.teacher.id,
                'name': ts.teacher.user.get_full_name(),
                'position': ts.teacher.position,
                'department': ts.teacher.department,
                'academic_degree': ts.teacher.academic_degree,
                'email': ts.teacher.user.email
            }
            
            subject_data = {
                'id': ts.subject.id,
                'name': ts.subject.name,
                'semester': ts.subject.semester,
                'description': ts.subject.description
            }
            
            result.append({
                'teacher': teacher_data,
                'subject': subject_data,
                'role': ts.role,
                'role_display': ts.get_role_display(),
                'is_main': ts.is_main
            })
        
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='service-token', permission_classes=[permissions.AllowAny])
    def service_token(self, request):
        """Эндпоинт для получения токена для межсервисного взаимодействия"""
        service_username = request.data.get('username')
        service_password = request.data.get('password')
        service_key = request.data.get('service_key')
        
        # Проверяем специальный ключ сервиса для дополнительной безопасности
        if service_key != 'student_performance_integration_key':
            return Response(
                {"detail": "Неверный ключ сервиса."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Проверяем учетные данные администратора
        if service_username != 'admin' or service_password != 'admin':
            return Response(
                {"detail": "Неверные учетные данные."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Получаем пользователя (администратора)
        user = User.objects.filter(is_staff=True).first()
        if not user:
            return Response(
                {"detail": "Не найдено ни одного администратора."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем токен для пользователя
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

# Добавляем публичное представление, полностью отключающее аутентификацию и проверку прав
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def public_teachers_api(request):
    """
    Публичный API для получения связей преподавателей с предметами.
    Полностью отключает аутентификацию и проверку прав.
    """
    try:
        # Получаем все активные связи
        teacher_subjects = SubjectTeacher.objects.all().order_by('id')
        
        # Формируем данные в удобном для студенческого портала формате
        result = []
        
        for ts in teacher_subjects:
            teacher_data = {
                'id': ts.teacher.id,
                'name': ts.teacher.user.get_full_name(),
                'position': ts.teacher.position,
                'department': ts.teacher.department,
                'academic_degree': ts.teacher.academic_degree,
                'email': ts.teacher.user.email
            }
            
            subject_data = {
                'id': ts.subject.id,
                'name': ts.subject.name,
                'semester': ts.subject.semester,
                'description': ts.subject.description
            }
            
            result.append({
                'teacher': teacher_data,
                'subject': subject_data,
                'role': ts.role,
                'role_display': ts.get_role_display(),
                'is_main': ts.is_main
            })
        
        # Принудительно создаем JSON с форматом даты по умолчанию
        json_data = json.dumps(result, default=str)
        
        # Возвращаем чистый HttpResponse с явными заголовками
        response = HttpResponse(
            content=json_data,
            content_type='application/json',
            status=200
        )
        
        # Добавляем заголовки для предотвращения кэширования и обхода CORS
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Access-Control-Allow-Origin'] = '*'
        response['Content-Type'] = 'application/json; charset=utf-8'
        
        return response
    except Exception as e:
        # Возвращаем ошибку в JSON формате
        error_data = {
            'error': 'Произошла ошибка при выполнении запроса',
            'details': str(e)
        }
        
        return HttpResponse(
            content=json.dumps(error_data),
            content_type='application/json',
            status=500
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def json_teachers_api(request):
    """
    Простой API для получения JSON-данных о преподавателях и их предметах.
    Доступен по короткому URL.
    """
    try:
        # Получение записей о связях преподавателей и предметов
        teacher_subject_relations = SubjectTeacher.objects.select_related('teacher', 'subject').all()
        
        # Формирование списка данных для ответа
        result = []
        for relation in teacher_subject_relations:
            teacher = relation.teacher
            subject = relation.subject
            
            result.append({
                'id': relation.id,
                'teacher': {
                    'id': teacher.id,
                    'name': teacher.user.get_full_name(),
                    'position': teacher.position,
                    'department': teacher.department
                },
                'subject': {
                    'id': subject.id,
                    'name': subject.name,
                    'semester': subject.semester
                },
                'role': relation.role,
                'role_display': relation.get_role_display(),
                'is_main': relation.is_main
            })
        
        # Возвращаем JSON-ответ
        return JsonResponse(result, safe=False)
    except Exception as e:
        # Возвращаем ошибку в JSON формате
        error_data = {
            'error': 'Произошла ошибка при выполнении запроса',
            'details': str(e)
        }
        
        return JsonResponse(error_data, status=500)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def raw_json_teachers_api(request):
    """
    Возвращает чистый JSON со списком преподавателей и их предметов.
    Этот API гарантированно возвращает JSON без HTML-разметки.
    """
    try:
        # Получение записей о связях преподавателей и предметов
        teacher_subject_relations = SubjectTeacher.objects.select_related('teacher', 'subject').all()
        
        # Формирование списка данных для ответа
        result = []
        for relation in teacher_subject_relations:
            teacher = relation.teacher
            subject = relation.subject
            
            result.append({
                'id': relation.id,
                'teacher_id': teacher.id,
                'teacher_full_name': teacher.user.get_full_name(),
                'subject_id': subject.id,
                'subject_name': subject.name,
                'subject_code': getattr(subject, 'code', ''),
                'role': relation.role,
                'is_main': relation.is_main
            })
        
        # Принудительно создаем JSON с форматом даты по умолчанию
        json_data = json.dumps(result, default=str)
        
        # Возвращаем чистый HttpResponse с явными заголовками
        response = HttpResponse(
            content=json_data,
            content_type='application/json',
            status=200
        )
        
        # Добавляем заголовки для предотвращения кэширования и обхода CORS
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Access-Control-Allow-Origin'] = '*'
        response['Content-Type'] = 'application/json; charset=utf-8'
        
        return response
    except Exception as e:
        # Логируем ошибку, но возвращаем JSON-ответ с информацией об ошибке
        error_data = {
            'error': 'Произошла ошибка при выполнении запроса',
            'details': str(e)
        }
        
        return HttpResponse(
            content=json.dumps(error_data),
            content_type='application/json',
            status=500
        )

def index_new(request):
    """
    Представление для новой главной страницы интерфейса преподавателя
    """
    context = {
        'courses_count': 5,
        'students_count': 127,
        'pending_submissions_count': 12,
        'today_classes_count': 3,
    }
    return render(request, 'teaching/index_new.html', context)

# Заглушки для представлений, используемых в навигации
def index(request):
    return render(request, 'teaching/index.html')

def schedule(request):
    return render(request, 'teaching/schedule.html')

def students(request):
    return render(request, 'teaching/students.html')

def grades(request):
    return render(request, 'teaching/grades.html')

def materials(request):
    return render(request, 'teaching/materials.html')

def messages_list(request):
    return render(request, 'teaching/messages.html')

def reports(request):
    return render(request, 'teaching/reports.html')

def settings(request):
    return render(request, 'teaching/settings.html')

def notifications(request):
    return render(request, 'teaching/notifications.html')

def search(request):
    query = request.GET.get('q', '')
    return render(request, 'teaching/search.html', {'query': query})

def course_create(request):
    return render(request, 'teaching/course_create.html')

def assignment_create(request):
    return render(request, 'teaching/assignment_create.html')

def material_upload(request):
    return render(request, 'teaching/material_upload.html')

@login_required
def subject_teacher_detail(request, subject_teacher_id):
    """
    Представление для просмотра детальной информации о связи преподаватель-предмет
    """
    teacher = get_object_or_404(Teacher, user=request.user)
    subject_teacher = get_object_or_404(SubjectTeacher, pk=subject_teacher_id)
    
    return render(request, 'teaching/subject_teacher_detail.html', {
        'teacher': teacher,
        'subject_teacher': subject_teacher
    })

class SubjectTeacherForm(forms.ModelForm):
    class Meta:
        model = SubjectTeacher
        fields = ['role', 'is_main', 'groups']

@login_required
def subject_teacher_edit(request, subject_teacher_id):
    """
    Представление для редактирования связи преподаватель-предмет
    """
    teacher = get_object_or_404(Teacher, user=request.user)
    subject_teacher = get_object_or_404(SubjectTeacher, pk=subject_teacher_id)
    subjects = Subject.objects.all()
    teachers = Teacher.objects.all()
    groups = Group.objects.all()
    
    if request.method == 'POST':
        form = SubjectTeacherForm(request.POST, instance=subject_teacher)
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher')
        groups_ids = request.POST.getlist('groups', [])
        
        if subject_id and teacher_id and form.is_valid():
            try:
                subject = Subject.objects.get(pk=subject_id)
                selected_teacher = Teacher.objects.get(pk=teacher_id)
                
                # Проверка наличия дубликатов, исключая текущую запись
                if not SubjectTeacher.objects.filter(subject=subject, teacher=selected_teacher).exclude(pk=subject_teacher_id).exists():
                    # Сохраняем форму, но пока не коммитим изменения
                    subject_teacher_obj = form.save(commit=False)
                    subject_teacher_obj.subject = subject
                    subject_teacher_obj.teacher = selected_teacher
                    subject_teacher_obj.save()
                    
                    # Сохраняем отношение many-to-many для групп
                    form.save_m2m()
                    
                    messages.success(request, f'Связь между преподавателем {selected_teacher.user.get_full_name()} и предметом {subject.name} успешно обновлена')
                    return redirect('subject_teachers')
                else:
                    messages.warning(request, 'Такая связь уже существует')
            except (Subject.DoesNotExist, Teacher.DoesNotExist):
                messages.error(request, 'Ошибка при обновлении связи: предмет или преподаватель не найден')
        else:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
    else:
        form = SubjectTeacherForm(instance=subject_teacher)
    
    return render(request, 'teaching/subject_teacher_edit.html', {
        'teacher': teacher,
        'subject_teacher': subject_teacher,
        'subjects': subjects,
        'teachers': teachers,
        'groups': groups,
        'form': form
    })
