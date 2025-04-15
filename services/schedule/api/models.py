from django.db import models


# Уберите все импорты из views или других модулей в начале файла
# Должны быть ТОЛЬКО модели

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Schedule(models.Model):
    DAY_CHOICES = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота')
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    day = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    subject = models.CharField(max_length=100)
    teacher = models.CharField(max_length=100)
    classroom = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day', 'start_time']