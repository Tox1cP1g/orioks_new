import django.db.models.deletion
from django.db import migrations, models


def add_vote_options(apps, schema_editor):
    # Получаем модель VoteOption через apps.get_model
    VoteOption = apps.get_model('user_dashboard', 'VoteOption')
    # Создаем записи с вариантами голосования
    VoteOption.objects.create(text="За")
    VoteOption.objects.create(text="Против")
    VoteOption.objects.create(text="Не уверен")


class Migration(migrations.Migration):

    initial = True

    # Убедитесь, что зависимость правильная, и 'user_dashboard' уже содержит миграцию до этой
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='VoteOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_dashboard.voteoption')),
            ],
        ),
        migrations.RunPython(add_vote_options),  # Добавляем варианты голосования после создания модели
    ]
