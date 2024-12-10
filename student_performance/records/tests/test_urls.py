from django.urls import reverse
from django.test import TestCase


class TestUrls(TestCase):

    def test_student_profile_url(self):
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
