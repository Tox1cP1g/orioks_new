from django.urls import path
from .views import GroupListView, ScheduleView

urlpatterns = [
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('schedule/', ScheduleView.as_view(), name='schedule-list'),
]