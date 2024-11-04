from django.shortcuts import render
from .models import Student, Course, Grade, Report
from django.db.models import Avg
from . import templates


def student_list(request):
    students = Student.objects.prefetch_related('grade_set', 'group').annotate(
        average_grade=Avg('grade__grade')  # Добавляем среднюю оценку
    )
    return render(request, 'student_list.html', {'students': students})


def course_list(request):
    courses = Course.objects.prefetch_related('professor').all()
    return render(request, 'course_list.html', {'courses': courses})


def grade_list(request):
    grades = Grade.objects.all()
    return render(request, 'grade_list.html', {'grades': grades})


def create_report(request, student_id, semester):
    student = Student.objects.get(id=student_id)
    grades = Grade.objects.filter(student=student, course__semester=semester)
    average_grade = grades.aggregate(models.Avg('grade'))['grade__avg']

    report = Report.objects.create(student=student, semester=semester, average_grade=average_grade)
    return render(request, 'records/report.html', {'report': report})
