from rest_framework import generics
from .models import Group, Schedule
from .serializers import GroupSerializer, ScheduleSerializer
from django.shortcuts import render

def schedule_view(request):
    try:
        groups = Group.objects.all()
        return render(request, 'schedule/index.html', {'groups': groups})
    except Exception as e:
        print(f"Error: {e}")  # Для отладки
        return render(request, 'schedule/index.html', {'groups': []})


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ScheduleView(generics.ListAPIView):
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get('group')
        if not group_id:
            return Schedule.objects.none()
        return Schedule.objects.filter(group_id=group_id)

    def get_queryset(self):
        group_id = self.request.query_params.get('group')
        return Schedule.objects.filter(group_id=group_id)