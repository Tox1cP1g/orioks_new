from django import forms
from .models import Homework, Professor


class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['title', 'professor', 'description', 'due_date']
