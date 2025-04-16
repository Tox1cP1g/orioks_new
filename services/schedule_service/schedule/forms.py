from django import forms
from .models import Schedule, Group

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['day_of_week', 'lesson_number', 'subject', 'teacher', 'room', 'group', 'semester', 'is_lecture']
        widgets = {
            'day_of_week': forms.Select(choices=Schedule.DAYS_OF_WEEK),
            'lesson_number': forms.NumberInput(attrs={'min': 1, 'max': 6}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'teacher': forms.TextInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.NumberInput(attrs={'min': 1, 'max': 8, 'class': 'form-control'}),
            'is_lecture': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 