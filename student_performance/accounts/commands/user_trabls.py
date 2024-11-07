from records.models import Student
from django.contrib.auth.models import User

# Найти студента, у которого user == None
students_without_user = Student.objects.filter(user__isnull=True)

# Присвоить пользователю, допустим, admin с ID 1
default_user = User.objects.get(id=1)

for student in students_without_user:
    student.user = default_user
    student.save()