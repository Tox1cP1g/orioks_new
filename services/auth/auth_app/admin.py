from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, WebAuthnCredential

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'student_id')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Личная информация'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Роль и специфичные поля'), {
            'fields': (
                'role',
                'student_id',
                'department',
                'position',
            ),
        }),
        (_('Права доступа'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'role',
                'first_name', 'last_name', 'email',
                'student_id', 'department', 'position'
            ),
        }),
    )

class WebAuthnCredentialAdmin(admin.ModelAdmin):
    list_display = ('credential_name', 'user', 'created_at', 'last_used_at')
    list_filter = ('user', 'created_at', 'last_used_at')
    search_fields = ('credential_name', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('id', 'credential_id', 'credential_public_key', 'sign_count', 'created_at', 'last_used_at')

admin.site.register(WebAuthnCredential, WebAuthnCredentialAdmin) 