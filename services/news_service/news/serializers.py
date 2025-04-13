from rest_framework import serializers
from .models import News  # Импорт модели News из текущего каталога

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'  # Сериализуем все поля модели