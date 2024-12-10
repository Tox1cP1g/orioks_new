from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Student, Group


class StudentProfileViewTest(TestCase):

    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(username='student_user', password='password')
        group = Group.objects.create(name="Group 1")
        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            group=group,
            user=self.user
        )
        self.client.login(username='student_user', password='password')

    def test_student_profile_view(self):
        # Проверяем, что профиль студента доступен
        url = reverse('student_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Мой профиль")
        self.assertContains(response, self.student.first_name)
e