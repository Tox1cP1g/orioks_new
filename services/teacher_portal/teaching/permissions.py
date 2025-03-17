from rest_framework import permissions

class IsTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'TEACHER' or request.user.is_staff)
        ) 