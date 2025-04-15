from django.core.management.base import BaseCommand
from performance.models import Group, Student
import uuid

class Command(BaseCommand):
    help = "Create a test student profile"

    def handle(self, *args, **options):
        self.stdout.write("Creating test student profile...")
        
        # Create or get a default group
        group, created = Group.objects.get_or_create(
            name="Тестовая группа",
            defaults={
                "faculty": "Тестовый факультет",
                "course": 1
            }
        )
        
        # Create a test student linked to user_id=1
        student, created = Student.objects.update_or_create(
            user_id=1,  # ID user (kobelev)
            defaults={
                "student_number": f"ST{uuid.uuid4().hex[:8].upper()}",
                "group": group,
                "faculty": "Тестовый факультет"
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f"Student profile created: {student.student_number}")) 