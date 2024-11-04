from django.contrib import admin
from .models import Student, Course, Grade
from import_export import resources


admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Grade)


class StudentResource(resources.ModelResource):
    class Meta:
        model = Student

# Register your models here.
