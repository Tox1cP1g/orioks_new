from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import StudentLoginForm, UserForm, ProfileForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .models import Profile
from records.models import Student  # Импортируем Student из records
from django.contrib.auth.forms import AuthenticationForm





# Create your views here.


# from django.contrib.auth.views import LoginView
#
# class CustomLoginView(LoginView):
#     template_name = 'accounts/student_login.html'



class StudentLoginView(LoginView):
    template_name = 'student_login.html'
    form_class = StudentLoginForm
    success_url = '/success/'  # Укажите путь к вашему успешному URL

    pass

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)

    def get_user(self):
        return self.cleaned_data.get('user')



# @login_required
# def profile_view(request):
#     # Получаем студента, связанного с текущим пользователем, или создаем нового, если его нет
#     student, created = Student.objects.get_or_create(user=request.user)
#
#     if request.method == 'POST':
#         user_form = UserForm(request.POST, instance=request.user)
#         profile_form = ProfileForm(request.POST, instance=student)
#
#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             profile_form.save()
#             return redirect('profile')
#     else:
#         user_form = UserForm(instance=request.user)
#         profile_form = ProfileForm(instance=student)
#
#     context = {
#         'user_form': user_form,
#         'profile_form': profile_form,
#         'student': student
#     }
#
#     return render(request, 'accounts/profile.html', context)
