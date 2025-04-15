import requests
from django.conf import settings
from rest_framework.exceptions import APIException

class GradesServiceClient:
    def __init__(self):
        self.base_url = settings.GRADES_SERVICE_URL
        self.headers = {
            'Authorization': f'Token {settings.GRADES_SERVICE_TOKEN}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method, endpoint, data=None, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIException(f"Ошибка при обращении к сервису оценок: {str(e)}")

    def get_student_grades(self, user_id):
        """Получить все оценки студента"""
        return self._make_request('GET', f'/api/students/{user_id}/grades/')

    def get_current_semester_grades(self, user_id):
        """Получить оценки студента за текущий семестр"""
        return self._make_request('GET', f'/api/students/{user_id}/current_semester_grades/')

    def get_subject_grades(self, subject_id):
        """Получить оценки по предмету"""
        return self._make_request('GET', f'/api/subjects/{subject_id}/grades/')

    def get_current_semester(self):
        """Получить текущий семестр"""
        return self._make_request('GET', '/api/semesters/current/')

    def get_student_info(self, user_id):
        """Получить информацию о студенте"""
        return self._make_request('GET', f'/api/students/{user_id}/') 