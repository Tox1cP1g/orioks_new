from django.test import TestCase
from records.forms import StudentForm
from records.models import Group


class StudentFormTest(TestCase):

    def setUp(self):
        # Создаем группу для студента
        Group.objects.create(name="Group 1")

    def test_student_form_valid(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'group': 'Group 1',
            'email': 'john.doe@example.com'
        }
        form = StudentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_student_form_invalid(self):
        form_data = {
            'first_name': '',
            'last_name': 'Doe',
            'group': 'Group 1',
            'email': 'john.doe@example.com'
        }
        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())у