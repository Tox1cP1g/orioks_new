# news/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('add/', views.add_news, name='add_news'),
    path('<int:news_id>/', views.news_detail, name='news_detail'),
]