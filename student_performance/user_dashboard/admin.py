from django.contrib import admin
from .models import VoteOption, Vote


# Register your models here.

@admin.register(VoteOption)
class VoteOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text')  # Для отображения в админке


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'ip_address', 'option')  # Для отображения в админке