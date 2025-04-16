from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from .utils import binary_to_string, string_to_binary

class User(AbstractUser):
    ROLE_CHOICES = [
        ('STUDENT', 'Студент'),
        ('TEACHER', 'Преподаватель'),
        ('ADMIN', 'Администратор'),
    ]
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='STUDENT',
        verbose_name="Роль пользователя"
    )
    student_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер студенческого")
    department = models.CharField(max_length=200, blank=True, null=True, verbose_name="Кафедра")
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="Должность")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

class WebAuthnCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webauthn_credentials')
    
    # Данные учетных данных WebAuthn
    credential_id = models.BinaryField(unique=True, verbose_name="ID учетных данных")
    credential_public_key = models.BinaryField(verbose_name="Публичный ключ")
    credential_name = models.CharField(max_length=100, verbose_name="Название ключа безопасности")
    
    # Метаданные
    sign_count = models.BigIntegerField(default=0, verbose_name="Счетчик подписей")
    rp_id = models.CharField(max_length=255, verbose_name="ID доверенной стороны")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name="Последнее использование")
    
    class Meta:
        verbose_name = "Ключ WebAuthn"
        verbose_name_plural = "Ключи WebAuthn"
        
    def __str__(self):
        return f"{self.credential_name} ({self.user.get_full_name()})"
    
    # Методы для работы с бинарными данными через base64
    def get_credential_id_binary(self):
        """Получить credential_id в бинарном виде для WebAuthn библиотеки"""
        return string_to_binary(self.credential_id)
    
    def set_credential_id_binary(self, binary_data):
        """Установить credential_id из бинарных данных, конвертируя в base64"""
        self.credential_id = binary_to_string(binary_data)
    
    def get_public_key_binary(self):
        """Получить credential_public_key в бинарном виде для WebAuthn библиотеки"""
        return string_to_binary(self.credential_public_key)
    
    def set_public_key_binary(self, binary_data):
        """Установить credential_public_key из бинарных данных, конвертируя в base64"""
        self.credential_public_key = binary_to_string(binary_data) 