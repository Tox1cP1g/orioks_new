from django.test import TestCase
from ..models import Student, Professor, Group


class StudentModelTest(TestCase):

    def setUp(self):
        # Создаем необходимые объекты для тестов
        group = Group.objects.create(name="Group 1")
        professor = Professor.objects.create(name="Professor A")

        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            group=group,
            professor=professor
        )

    def test_student_creation(self):
        # Проверяем, что студент был успешно создан
        self.assertEqual(self.student.first_name, "John")
        self.assertEqual(self.student.last_name, "Doe")
        self.assertEqual(self.student.group.name, "Group 1")

    def test_student_str(self):
        # Проверяем, что строковое представление студента корректно
        self.assertEqual(str(self.student), "John Doe")
