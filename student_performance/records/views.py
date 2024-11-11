from django.shortcuts import render, get_object_or_404
from .models import Student, Course, Grade, Report
from django.db.models import Avg
from . import templates


def student_list(request):
    students = Student.objects.prefetch_related('grade_set', 'group').annotate(
        average_grade=Avg('grade__grade')  # Добавляем среднюю оценку
    )
    return render(request, 'student_list.html', {'students': students})

def subjects_list(request):
    subjects = Course.objects.prefetch_related('professor').all()
    return render(request, 'subjects_list.html', {'courses': subjects})



def course_list(request):
    courses = Course.objects.prefetch_related('professor').all()
    return render(request, 'course_list.html', {'courses': courses})


def grade_list(request):
    course_id = request.GET.get('course', None)
    if course_id:
        grades = Grade.objects.filter(course_id=course_id)
    else:
        grades = Grade.objects.all()

    courses = Course.objects.all()  # Получаем список всех предметов
    return render(request, 'grade_list.html', {'grades': grades, 'courses': courses})


# def create_report(request, student_id, semester):
#     student = Student.objects.get(id=student_id)
#     grades = Grade.objects.filter(student=student, course__semester=semester)
#     average_grade = grades.aggregate(models.Avg('grade'))['grade__avg']
#
#     report = Report.objects.create(student=student, semester=semester, average_grade=average_grade)
#     return render(request, 'records/report.html', {'report': report})

def student_report_view(request):
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


def grades_view(request):
    grades = Grade.objects.all()  # Получаем все оценки
    return render(request, 'grades.html', {
        'grades': grades,
    })


from django.shortcuts import render
from .models import Student, Grade


def grades_info(request):
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
