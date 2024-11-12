from django import forms
from django.contrib.auth.forms import AuthenticationForm
from records.models import Student  # Импортируем Student из records
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth import authenticate

from django import forms
from django.contrib.auth import authenticate


# from django import forms
# from django.contrib.auth import authenticate

class StudentLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        # Пытаемся аутентифицировать пользователя
        user = authenticate(username=username, password=password)
        if user is None:
            raise forms.ValidationError("Неверное имя пользователя или пароль.")
        return cleaned_data



class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['student_id', 'bio', 'location', 'birth_date']


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