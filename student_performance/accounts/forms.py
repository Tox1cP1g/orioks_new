from django import forms
from django.contrib.auth.forms import AuthenticationForm
from records.models import Student  # Импортируем Student из records


class StudentLoginForm(AuthenticationForm):
    student_id = forms.CharField(max_length=20, label='ID студента')

    def clean(self):
        cleaned_data = super().clean()
        student_id = cleaned_data.get('student_id')

        if student_id:
            try:
                student = Student.objects.get(student_id=student_id)
            except Student.DoesNotExist:
                raise forms.ValidationError("Студент с таким ID не найден.")

        return cleaned_data


# class ProfessorLoginForm(AuthenticationForm):
#     professor_id = forms.CharField(label="ID сотрудника", max_length=20)
#
#     def clean(self):
#         cleaned_data = super().clean()
#         professor_id = cleaned_data.get("professor_id")
#         if professor_id:
#             try:
#                 professor = Professor.objects.get(user__username=professor_id)
#                 cleaned_data['username'] = professor.user.username
#             except Professor.DoesNotExist:
#                 raise forms.ValidationError("Пользователь с таким ID не найден.")
#         return cleaned_data