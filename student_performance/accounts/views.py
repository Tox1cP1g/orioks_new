from django.shortcuts import render
from django.contrib.auth import login
from .forms import StudentLoginForm
from django.contrib.auth.views import LoginView

# Create your views here.


# from django.contrib.auth.views import LoginView
#
# class CustomLoginView(LoginView):
#     template_name = 'accounts/student_login.html'


class StudentLoginView(LoginView):
    template_name = 'student_login.html'
    form_class = StudentLoginForm
    success_url = '/success/'  # Укажите путь к вашему успешному URL

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)