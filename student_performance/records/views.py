from django.shortcuts import render, get_object_or_404, redirect
from .models import Student, Course, Grade, Report, Professor, Homework, HomeworkFile, Schedule
from django.db.models import Avg
from .forms import HomeworkForm
from django.contrib.auth.decorators import login_required
from django.http import Http404
from . import templates


def student_list(request):
    if request.user.is_superuser or request.user.is_staff:
        students = Student.objects.prefetch_related('grade_set', 'group').annotate(
            average_grade=Avg('grade__grade')  # Добавляем среднюю оценку
        )
        return render(request, 'student_list.html', {'students': students})
    raise Http404("Страница не найдена")



def subjects_list(request):
    # Получаем студента, связанного с текущим пользователем
    try:
        student = Student.objects.get(user=request.user)  # Предполагается связь user-Student
    except Student.DoesNotExist:
        student = None

    # Получаем список предметов с оценками для конкретного студента
    courses = Course.objects.prefetch_related('professor').all()

    return render(request, 'subjects_list.html', {'student': student, 'courses': courses})



def course_list(request):
    if request.user.is_superuser or request.user.is_staff:
        courses = Course.objects.prefetch_related('professor').all()
        return render(request, 'course_list.html', {'courses': courses})
    raise Http404("Страница не найдена")


def grade_list(request):
    if request.user.is_superuser or request.user.is_staff:
        course_id = request.GET.get('course', None)
        if course_id:
            grades = Grade.objects.filter(course_id=course_id)
        else:
            grades = Grade.objects.all()

        courses = Course.objects.all()  # Получаем список всех предметов
        return render(request, 'grade_list.html', {'grades': grades, 'courses': courses})
    raise Http404("Страница не найдена")


# def create_report(request, student_id, semester):
#     student = Student.objects.get(id=student_id)
#     grades = Grade.objects.filter(student=student, course__semester=semester)
#     average_grade = grades.aggregate(models.Avg('grade'))['grade__avg']
#
#     report = Report.objects.create(student=student, semester=semester, average_grade=average_grade)
#     return render(request, 'records/report.html', {'report': report})

def student_report_view(request):
    if request.user.is_superuser or request.user.is_staff:
        students = Student.objects.all()  # Получаем список всех студентов
        selected_student = None
        grades = []

        if request.GET.get('student'):
            selected_student = get_object_or_404(Student, id=request.GET['student'])
            grades = Grade.objects.filter(student=selected_student)

        return render(request, 'student_report.html', {
            'students': students,
            'selected_student': selected_student,
            'grades': grades,
        })
    raise Http404("Страница не найдена")



def grades_view(request):
    grades = Grade.objects.all()  # Получаем все оценки
    return render(request, 'grades.html', {
        'grades': grades,
    })


from django.shortcuts import render
from .models import Student, Grade, Internship


def grades_info(request):
    if request.user.is_superuser or request.user.is_staff:
        student_id = request.GET.get('student', None)

        if student_id:
            # Фильтруем оценки по студенту
            grades = Grade.objects.filter(student__id=student_id)
        else:
            # Если студент не выбран, выводим все оценки
            grades = Grade.objects.all()

        # Получаем всех студентов для выпадающего списка
        students = Student.objects.all()

        return render(request, 'grades_info.html', {
            'grades': grades,
            'students': students,
        })
    raise Http404("Страница не найдена")

def internship_list(request):
    internships = Internship.objects.all()
    return render(request, 'internship_list.html', {'internships': internships})


def create_homework(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST, request.FILES)
        if form.is_valid():
            # Сохраняем домашку
            homework = form.save(commit=False)
            homework.user = request.user  # Назначаем текущего пользователя как создателя
            homework.save()

            # Сохраняем файлы
            files = request.FILES.getlist('files')
            for file in files:
                HomeworkFile.objects.create(homework=homework, file=file)

            return redirect('homework_list')
    else:
        form = HomeworkForm()

    return render(request, 'create_homework.html', {'form': form})


def homework_list(request):
    homeworks = Homework.objects.filter(user=request.user)
    print(homeworks)
    homeworks_new = HomeworkFile.objects.filter(homework__user=request.user)
    print(homeworks_new, '1111')
    return render(request, 'homework_list.html', {'homeworks': homeworks, 'homeworks_new': homeworks_new})


@login_required
def profile(request):
    try:
        # Пытаемся получить профиль студента для текущего пользователя
        student = Student.objects.get(user=request.user)  # Предполагается связь user-Student
    except Student.DoesNotExist:
        # Если профиль не существует, создаем новый
        student = None

    return render(request, 'profile.html', {'student_profile': student})


@login_required
def profile_staff(request):
    if request.user.is_superuser or request.user.is_staff:
        try:
            # Пытаемся получить профиль студента для текущего пользователя
            professor = Professor.objects.get(user=request.user)  # Предполагается связь user-Student
        except Professor.DoesNotExist:
            # Если профиль не существует, создаем новый
            professor = None

        return render(request, 'profile_staff.html', {'professor_profile': professor})
    raise Http404("Страница не найдена")


def help_students(request):
    return render(request, 'help_students.html')


def schedule_view(request):
    schedule = Schedule.objects.all().order_by('day_of_week', 'time')
    return render(request, 'schedule.html', {'schedule': schedule})