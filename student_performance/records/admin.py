from django.contrib import admin
from .models import Student, Course, Grade, Group, Professor
from import_export import resources


admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Grade)
admin.site.register(Group)
admin.site.register(Professor)


class StudentResource(resources.ModelResource):
    class Meta:
        model = Student


# class StudentAdmin(admin.ModelAdmin):
#     def username(self, obj):
#         return obj.user.username if obj.user else 'Нет пользователя'
#
#     list_display = ('username',)  # или другие поля


# admin.site.register(StudentAdmin)
# Register your models here.
