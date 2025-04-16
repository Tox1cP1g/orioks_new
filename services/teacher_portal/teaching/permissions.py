from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist
from .models import Teacher

class IsTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Администраторы всегда имеют доступ
        if request.user.is_staff:
            return True
            
        # Проверяем, есть ли у пользователя связанная модель Teacher
        try:
            teacher = Teacher.objects.get(user=request.user)
            return True
        except ObjectDoesNotExist:
            return False 