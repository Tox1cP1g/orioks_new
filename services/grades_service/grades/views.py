import logging
import json
from datetime import datetime, timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny

from .models import Semester, Subject, Student, Grade, Group, Teacher
from .services import sync_teachers_from_portal, sync_students_and_groups_from_portal

logger = logging.getLogger(__name__)

def test_redirect(request):
    """Тестовая функция для проверки перенаправлений"""
    logger.info(f"TEST REDIRECT: path={request.path}, full_path={request.get_full_path()}")
    logger.info(f"TEST REDIRECT: GET params={request.GET}")
    logger.info(f"TEST REDIRECT: META HTTP_HOST={request.META.get('HTTP_HOST', 'unknown')}")
    
    host = request.META.get('HTTP_HOST', 'unknown')
    path = request.path
    full_path = request.get_full_path()
    
    html = f"""
    <html>
        <head><title>Тест перенаправления</title></head>
        <body>
            <h1>Детали запроса:</h1>
            <ul>
                <li>Host: {host}</li>
                <li>Path: {path}</li>
                <li>Full Path: {full_path}</li>
            </ul>
            <h2>Тестовые ссылки:</h2>
            <ul>
                <li><a href="http://localhost:8005/8004/">Страница преподавателя</a></li>
                <li><a href="http://localhost:8005/8003/">Страница студента</a></li>
            </ul>
        </body>
    </html>
    """
    return HttpResponse(html)

@ensure_csrf_cookie
def index(request):
    """Главная страница сервиса оценок"""
    full_path = request.get_full_path().lower()
    
    # Проверяем порты в URL для перенаправления
    if '8003' in full_path or '4003' in full_path:
        logger.info(f"Index detected student port in URL, redirecting to student portal")
        return direct_to_student_portal(request)
    if '8004' in full_path or '4004' in full_path:
        logger.info(f"Index detected teacher port in URL, redirecting to teacher portal")
        return direct_to_teacher_portal(request)
    
    if not request.user.is_authenticated:
        logger.warning("User not authenticated, redirecting to login")
        return HttpResponseRedirect('http://localhost:8002/login/')
    
    logger.info(f"User accessing index: {request.user.username}, role: {request.user.role}")
    
    if hasattr(request.user, 'role') and request.user.role == 'TEACHER':
        logger.info("User is TEACHER, redirecting to teacher_grades")
        return redirect('teacher_grades')
    else:
        logger.info("User is STUDENT, redirecting to student_grades")
        return redirect('student_grades')

@ensure_csrf_cookie
def student_grades(request):
    """
    View для отображения страницы оценок студента.
    Проверяет аутентификацию и роль пользователя.
    """
    if not request.user.is_authenticated:
        logger.warning("User not authenticated, redirecting to login")
        return redirect('http://localhost:8002/login/')

    logger.info(f"User accessing student grades: {request.user.username}, "
               f"role: {getattr(request.user, 'role', 'unknown')}, "
               f"authenticated: {request.user.is_authenticated}")

    # Проверка роли пользователя (должен быть студентом)
    if hasattr(request.user, 'role') and request.user.role != 'STUDENT':
        logger.warning(f"User {request.user.username} with role {request.user.role} tried to access student grades")
        messages.warning(request, "Доступ ограничен. Перенаправление на соответствующий портал.")
        return redirect('http://localhost:8004/dashboard/' if request.user.role == 'TEACHER' else 'http://localhost:8003/dashboard/')

    # Получаем список семестров, отсортированный по дате начала
    semesters = Semester.objects.all().order_by('-start_date')
    
    # Проверяем наличие семестров
    if not semesters.exists() and settings.DEBUG:
        # Создаем тестовый семестр, если нет семестров и включен режим отладки
        from datetime import datetime, timedelta
        today = datetime.now()
        start_date = today - timedelta(days=30)
        end_date = today + timedelta(days=90)
        semester = Semester.objects.create(
            name="Текущий семестр",
            start_date=start_date,
            end_date=end_date,
            is_current=True
        )
        semesters = Semester.objects.all()
        logger.warning("Created test semester for debugging")
    
    # Пробуем получить данные о студенте из портала студентов через token
    token = request.COOKIES.get('token')
    
    # Пытаемся найти или создать запись студента
    try:
        # Используем id вместо user_id для совместимости
        student = Student.objects.get(user_id=request.user.id)
        student_group = student.group.name if student.group else "Не назначена"
        student_group_id = student.group.id if student.group else None
    except Student.DoesNotExist:
        # Пробуем создать запись студента на основе данных пользователя
        logger.warning(f"No student record found for user {request.user.username}, creating new one")
        try:
            # Синхронизируем данные из портала студентов
            sync_students_and_groups_from_portal(token)
            
            # Проверяем, появился ли студент после синхронизации
            try:
                student = Student.objects.get(user_id=request.user.id)
                student_group = student.group.name if student.group else "Не назначена"
                student_group_id = student.group.id if student.group else None
                logger.info(f"Found student record after sync: {student.get_full_name()}")
            except Student.DoesNotExist:
                # Если после синхронизации студент не найден, используем существующую логику
                # Берем первую группу из списка, если они есть
                group = Group.objects.first()
                if not group and settings.DEBUG:
                    # Создаем группу, если нет ни одной
                    group = Group.objects.create(name="Новые студенты")
                    logger.warning("Created test group for debugging")
                
                student = Student.objects.create(
                    user_id=request.user.id,
                    first_name=getattr(request.user, 'first_name', request.user.username),
                    last_name=getattr(request.user, 'last_name', ''),
                    email=getattr(request.user, 'email', ''),
                    group=group
                )
                student_group = group.name if group else "Не назначена"
                student_group_id = group.id if group else None
                logger.info(f"Created new student record for user {request.user.username}")
        except Exception as e:
            student_group = "Не назначена"
            student_group_id = None
            logger.error(f"Error creating student record: {str(e)}")
    
    # Получаем все группы для отображения в интерфейсе
    groups = Group.objects.all()

    context = {
        'semesters': semesters,
        'student_group': student_group,
        'student_group_id': student_group_id,
        'groups': groups,
    }

    return render(request, 'grades/student_grades.html', context)

@ensure_csrf_cookie
def teacher_grades(request):
    """Управление оценками для преподавателя"""
    try:
        logger.info(f"ТЕST: Accessing teacher_grades view. Path: {request.path}, Full path: {request.get_full_path()}")
        logger.info(f"ТЕST: User authenticated: {request.user.is_authenticated}, User: {request.user}")
        
        # В режиме отладки можем создать фейкового пользователя-преподавателя для отладки шаблона
        if settings.DEBUG and not request.user.is_authenticated:
            from django.contrib.auth.models import AnonymousUser
            class DebugTeacherUser(AnonymousUser):
                is_authenticated = True
                username = "debug_teacher"
                first_name = "Debug"
                last_name = "Teacher"
                email = "debug@example.com"
                role = "TEACHER"
                is_staff = True
                is_superuser = False
                
            logger.warning("Creating debug teacher user for template rendering in DEBUG mode")
            request.user = DebugTeacherUser()
        
        if not request.user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return HttpResponseRedirect('http://localhost:8002/login/')
        
        logger.info(f"User accessing teacher_grades: {request.user.username}, role: {getattr(request.user, 'role', 'unknown')}")
        
        if not hasattr(request.user, 'role') or request.user.role != 'TEACHER':
            if settings.DEBUG:
                logger.warning("Non-teacher accessing teacher page in DEBUG mode")
                messages.warning(request, "Вы не являетесь преподавателем (DEBUG режим)")
            else:
                logger.warning("Non-teacher trying to access teacher page")
                messages.error(request, "У вас нет прав для просмотра этой страницы")
                return redirect('http://localhost:8004/dashboard/')
        
        # Получаем token из cookies для доступа к API
        token = request.COOKIES.get('token')
        
        # Пробуем найти или создать запись преподавателя
        try:
            teacher = Teacher.objects.get(user_id=request.user.id)
            logger.info(f"Found teacher record: {teacher.get_full_name()}")
        except Teacher.DoesNotExist:
            # Синхронизируем данные из портала преподавателей
            sync_teachers_from_portal(token)
            
            # Проверяем, появился ли преподаватель после синхронизации
            try:
                teacher = Teacher.objects.get(user_id=request.user.id)
                logger.info(f"Found teacher record after sync: {teacher.get_full_name()}")
            except Teacher.DoesNotExist:
                # Если не найден, создаем запись преподавателя на основе данных пользователя
                teacher = Teacher.objects.create(
                    user_id=request.user.id,
                    first_name=getattr(request.user, 'first_name', ''),
                    last_name=getattr(request.user, 'last_name', ''),
                    email=getattr(request.user, 'email', ''),
                    department='Не указана',
                    position='Преподаватель'
                )
                logger.warning(f"Created teacher record for user {request.user.username}")
        
        # Получаем список семестров
        semesters = Semester.objects.all().order_by('-start_date')
        if not semesters.exists():
            # Если нет семестров, создаем тестовый семестр
            if settings.DEBUG:
                from datetime import datetime, timedelta
                today = datetime.now()
                start_date = today - timedelta(days=30)
                end_date = today + timedelta(days=90)
                semester = Semester.objects.create(
                    name="Текущий семестр",
                    start_date=start_date,
                    end_date=end_date,
                    is_current=True
                )
                semesters = Semester.objects.all()
                logger.warning("Created test semester for debugging")
        
        selected_semester = Semester.objects.filter(is_current=True).first() or semesters.first()
        
        # Синхронизируем данные студентов и групп
        sync_students_and_groups_from_portal(token)
        
        # Получаем все группы для отображения в интерфейсе
        groups = Group.objects.all()
        
        context = {
            'semesters': semesters,
            'selected_semester': selected_semester,
            'groups': groups,
            'teacher': teacher,
        }
        
        logger.info("Rendering teacher_grades.html template")
        return render(request, 'grades/teacher_grades.html', context)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке teacher_grades: {str(e)}")
        messages.error(request, f"Произошла ошибка при загрузке данных: {str(e)}")
        context = {'error': str(e)}
        return render(request, 'grades/teacher_grades.html', context)

@ensure_csrf_cookie
def edit_grade(request, grade_id):
    """Редактирование оценки"""
    if not request.user.is_authenticated:
        return HttpResponseRedirect('http://localhost:8002/login/')
    
    if not hasattr(request.user, 'role') or request.user.role != 'TEACHER':
        messages.error(request, "У вас нет прав для редактирования оценок")
        return redirect('index')
    
    grade = get_object_or_404(Grade, id=grade_id)
    
    if request.method == 'POST':
        grade_type = request.POST.get('grade_type')
        score = request.POST.get('score')
        max_score = request.POST.get('max_score')
        date = request.POST.get('date')
        comment = request.POST.get('comment')
        
        if not all([grade_type, score, max_score, date]):
            messages.error(request, "Пожалуйста, заполните все обязательные поля")
            return redirect(request.path)
        
        try:
            grade.grade_type = grade_type
            grade.score = float(score)
            grade.max_score = float(max_score)
            grade.date = datetime.strptime(date, '%Y-%m-%d').date()
            grade.comment = comment
            grade.save()
            
            messages.success(request, "Оценка успешно обновлена")
            return redirect('teacher_grades')
        except Exception as e:
            messages.error(request, f"Ошибка при обновлении оценки: {str(e)}")
    
    return render(request, 'edit_grade.html', {'grade': grade})

def logout(request):
    """Перенаправление на портал преподавателя с сохранением токена"""
    token = request.COOKIES.get('token')
    logger.info("Redirecting to teacher portal (8004)")
    
    if token:
        logger.info("Token found, preserving for redirect")
    else:
        logger.warning("No token found in request cookies")
    
    response = HttpResponseRedirect('http://localhost:8004/dashboard/')
    
    if token:
        response.set_cookie(
            'token',
            token,
            domain='localhost',
            path='/',
            secure=False,
            httponly=True,
            samesite='Lax',
            max_age=86400  # 24 часа
        )
        logger.info("Token cookie set for localhost domain")
    
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

def direct_to_teacher_portal(request):
    """Прямое перенаправление на портал преподавателя"""
    logger.info(f"Redirecting to teacher portal from: {request.get_full_path()}")
    response = HttpResponseRedirect('http://localhost:8004/dashboard/')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def direct_to_student_portal(request):
    """Прямое перенаправление на портал студента"""
    logger.info(f"Redirecting to student portal from: {request.get_full_path()}")
    response = HttpResponseRedirect('http://localhost:8003/dashboard/')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@require_http_methods(["GET"])
def get_student_grades(request, semester_id):
    """
    API endpoint для получения оценок студента за выбранный семестр.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        # В режиме разработки не требуем строгой проверки роли
        if not settings.DEBUG and (not hasattr(request.user, 'role') or request.user.role != 'STUDENT'):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        # Пытаемся найти студента по user_id
        try:
            # Используем request.user.id вместо user_id
            student = Student.objects.get(user_id=request.user.id)
        except Student.DoesNotExist:
            # В режиме разработки создаем студента, если его нет
            if settings.DEBUG:
                logger.warning(f"Creating new student for user {request.user.username}")
                group, _ = Group.objects.get_or_create(name="Test Group")
                student = Student.objects.create(
                    user_id=getattr(request.user, 'id', 'test_id'),
                    first_name=getattr(request.user, 'first_name', ''),
                    last_name=getattr(request.user, 'last_name', ''),
                    email=getattr(request.user, 'email', ''),
                    group=group
                )
            else:
                logger.error(f"No student record found for user {request.user.username}")
                return JsonResponse({'error': 'Student not found'}, status=404)
        
        # Получаем семестр
        semester = Semester.objects.get(id=semester_id)
        
        # Получаем оценки студента за семестр
        grades = Grade.objects.filter(
            student=student,
            subject__semester=semester
        ).select_related('subject')
        
        # Формируем данные для ответа
        grades_data = [{
            'subject_name': grade.subject.name,
            'teacher_name': grade.subject.teacher.get_full_name() if grade.subject.teacher else 'Не указан',
            'value': grade.value,
            'date': grade.date.strftime('%d.%m.%Y')
        } for grade in grades]

        # Если нет оценок, в режиме разработки можем создать тестовые
        if not grades_data and settings.DEBUG:
            logger.warning(f"No grades found for student {student.get_full_name()} in semester {semester.name}")
            
            # Создаем тестовую оценку если нет оценок и мы в режиме DEBUG
            if settings.CREATE_TEST_DATA:
                subject, _ = Subject.objects.get_or_create(
                    name="Test Subject",
                    semester=semester
                )
                grade = Grade.objects.create(
                    student=student,
                    subject=subject,
                    value=85.0,
                    date=timezone.now().date(),
                    created_by="System"
                )
                grades_data.append({
                    'subject_name': grade.subject.name,
                    'teacher_name': 'Тестовый преподаватель',
                    'value': grade.value,
                    'date': grade.date.strftime('%d.%m.%Y')
                })

        return JsonResponse(grades_data, safe=False)
    except Semester.DoesNotExist:
        return JsonResponse({'error': 'Semester not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting student grades: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_http_methods(["GET"])
def get_groups(request, semester_id):
    """
    API endpoint для получения списка групп для выбранного семестра.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        # В режиме разработки не требуем строгой проверки роли
        if not settings.DEBUG and (not hasattr(request.user, 'role') or request.user.role != 'TEACHER'):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        # Получаем все группы, независимо от семестра для упрощения тестирования
        groups = Group.objects.all()
        
        logger.info(f"Found {groups.count()} groups for semester_id={semester_id}")
        
        groups_data = [{
            'id': group.id,
            'name': group.name,
            'department': group.department or 'Не указан'
        } for group in groups]
        
        return JsonResponse(groups_data, safe=False)
    except Exception as e:
        logger.error(f"Error getting groups: {str(e)}")
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def get_grades(request, group_id):
    """
    API endpoint для получения оценок студентов выбранной группы.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        # В режиме разработки не требуем строгой проверки роли
        if not settings.DEBUG and (not hasattr(request.user, 'role') or request.user.role != 'TEACHER'):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        group = Group.objects.get(id=group_id)
        
        # В режиме разработки можем получить всех студентов группы, даже если у них нет оценок
        students = Student.objects.filter(group=group)
        
        # Получаем оценки для всех студентов группы
        grades = Grade.objects.filter(
            student__in=students
        ).select_related('student', 'subject')
        
        grades_data = [{
            'id': grade.id,
            'student_name': grade.student.get_full_name(),
            'subject_name': grade.subject.name,
            'value': grade.value,
            'max_value': grade.max_value,
            'date': grade.date.strftime('%d.%m.%Y')
        } for grade in grades]

        # Если нет оценок, можем вернуть пустой список
        if not grades_data and settings.DEBUG:
            logger.warning(f"No grades found for group {group.name}")

        return JsonResponse(grades_data, safe=False)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting grades: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_http_methods(["POST"])
def add_grade(request):
    """
    API endpoint для добавления новой оценки.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if not hasattr(request.user, 'role') or request.user.role != 'TEACHER':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)
        required_fields = ['student_id', 'subject_id', 'value', 'max_value', 'date']
        
        if not all(field in data for field in required_fields):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        student = Student.objects.get(id=data['student_id'])
        subject = Subject.objects.get(id=data['subject_id'])

        grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=float(data['value']),
            max_value=float(data['max_value']),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            comment=data.get('comment', ''),
            created_by=request.user.username
        )

        return JsonResponse({
            'success': True,
            'grade_id': grade.id
        })
    except (Student.DoesNotExist, Subject.DoesNotExist):
        return JsonResponse({'error': 'Student or subject not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error adding grade: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_http_methods(["DELETE"])
def delete_grade(request, grade_id):
    """
    API endpoint для удаления оценки.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if not hasattr(request.user, 'role') or request.user.role != 'TEACHER':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        grade = Grade.objects.get(id=grade_id)
        grade.delete()
        return JsonResponse({'success': True})
    except Grade.DoesNotExist:
        return JsonResponse({'error': 'Grade not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting grade: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_http_methods(["POST"])
def set_student_group(request):
    """
    API endpoint для изменения группы студента.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        if not group_id:
            return JsonResponse({'error': 'Missing group_id parameter'}, status=400)
        
        # Получаем объект группы
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return JsonResponse({'error': 'Group not found'}, status=404)
        
        # Получаем или создаем запись студента
        student, created = Student.objects.get_or_create(
            user_id=request.user.id,
            defaults={
                'first_name': getattr(request.user, 'first_name', ''),
                'last_name': getattr(request.user, 'last_name', ''),
                'email': getattr(request.user, 'email', '')
            }
        )
        
        # Обновляем группу студента
        student.group = group
        student.save()
        
        logger.info(f"Changed group for student {student.get_full_name()} to {group.name}")
        
        return JsonResponse({
            'success': True,
            'group_id': group.id,
            'group_name': group.name
        })
        
    except Exception as e:
        logger.error(f"Error setting student group: {str(e)}")
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

@staff_member_required
def sync_data_from_portals(request):
    """
    Функция для ручной синхронизации данных из порталов студентов и преподавателей.
    Доступна только администраторам через админку.
    """
    try:
        token = request.COOKIES.get('token')
        
        # Синхронизируем данные преподавателей
        teachers_count = sync_teachers_from_portal(token)
        
        # Синхронизируем данные студентов и групп
        groups_count, students_count = sync_students_and_groups_from_portal(token)
        
        messages.success(
            request, 
            f"Данные успешно синхронизированы. Обновлено/добавлено: "
            f"{teachers_count} преподавателей, {groups_count} групп, {students_count} студентов."
        )
    except Exception as e:
        logger.error(f"Ошибка при синхронизации данных: {str(e)}")
        messages.error(request, f"Ошибка при синхронизации данных: {str(e)}")
    
    # Возвращаемся на предыдущую страницу
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def get_groups_api(request):
    """
    API endpoint для получения списка групп.
    """
    try:
        # Получаем все группы
        groups = Group.objects.all()
        
        # Формируем данные для ответа
        result = []
        for group in groups:
            result.append({
                'id': group.id,
                'name': group.name,
                'department': group.department or 'Не указан',
                'students_count': group.students.count()
            })
        
        # Возвращаем чистый HttpResponse с явными заголовками
        response = HttpResponse(
            content=json.dumps(result, default=str),
            content_type='application/json',
            status=200
        )
        
        # Добавляем заголовки для предотвращения кэширования и обхода CORS
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Access-Control-Allow-Origin'] = '*'
        response['Content-Type'] = 'application/json; charset=utf-8'
        
        return response
    except Exception as e:
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
@permission_classes([AllowAny])
@authentication_classes([])
def get_students_by_group_api(request, group_id):
    """
    API endpoint для получения списка студентов в группе.
    """
    try:
        # Получаем группу
        group = Group.objects.get(id=group_id)
        
        # Получаем студентов группы
        students = group.students.all()
        
        # Формируем данные для ответа
        result = {
            'group': {
                'id': group.id,
                'name': group.name,
                'department': group.department or 'Не указан'
            },
            'students': [
                {
                    'id': student.id,
                    'full_name': f"{student.last_name} {student.first_name}",
                    'email': student.email,
                    'student_id': getattr(student, 'student_id', None)
                }
                for student in students
            ]
        }
        
        # Возвращаем чистый HttpResponse с явными заголовками
        response = HttpResponse(
            content=json.dumps(result, default=str),
            content_type='application/json',
            status=200
        )
        
        # Добавляем заголовки для предотвращения кэширования и обхода CORS
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Access-Control-Allow-Origin'] = '*'
        response['Content-Type'] = 'application/json; charset=utf-8'
        
        return response
    except Group.DoesNotExist:
        error_data = {
            'error': 'Группа не найдена',
            'details': f'Группа с ID {group_id} не существует'
        }
        return HttpResponse(
            content=json.dumps(error_data),
            content_type='application/json',
            status=404
        )
    except Exception as e:
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
@permission_classes([AllowAny])
@authentication_classes([])
def get_semesters_api(request):
    """
    API endpoint для получения списка семестров.
    """
    try:
        # Получаем все семестры
        semesters = Semester.objects.all().order_by('-start_date')
        
        # Формируем данные для ответа
        result = []
        for semester in semesters:
            result.append({
                'id': semester.id,
                'name': semester.name,
                'start_date': semester.start_date.strftime('%Y-%m-%d'),
                'end_date': semester.end_date.strftime('%Y-%m-%d'),
                'is_current': semester.is_current
            })
        
        # Возвращаем чистый HttpResponse с явными заголовками
        response = HttpResponse(
            content=json.dumps(result, default=str),
            content_type='application/json',
            status=200
        )
        
        # Добавляем заголовки для предотвращения кэширования и обхода CORS
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Access-Control-Allow-Origin'] = '*'
        response['Content-Type'] = 'application/json; charset=utf-8'
        
        return response
    except Exception as e:
        error_data = {
            'error': 'Произошла ошибка при выполнении запроса',
            'details': str(e)
        }
        return HttpResponse(
            content=json.dumps(error_data),
            content_type='application/json',
            status=500
        )
