from rest_framework import serializers
from .models import Group, Schedule


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class ScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = Schedule
        fields = ['day', 'day_name', 'subject', 'teacher', 'classroom', 'start_time', 'end_time']