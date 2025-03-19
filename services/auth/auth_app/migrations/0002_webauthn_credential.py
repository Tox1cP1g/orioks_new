import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebAuthnCredential',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('credential_id', models.CharField(max_length=255, unique=True, verbose_name='ID учетных данных')),
                ('credential_public_key', models.TextField(verbose_name='Публичный ключ')),
                ('credential_name', models.CharField(max_length=100, verbose_name='Название ключа безопасности')),
                ('sign_count', models.BigIntegerField(default=0, verbose_name='Счетчик подписей')),
                ('rp_id', models.CharField(max_length=255, verbose_name='ID доверенной стороны')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='Последнее использование')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webauthn_credentials', to='auth_app.user')),
            ],
            options={
                'verbose_name': 'Ключ WebAuthn',
                'verbose_name_plural': 'Ключи WebAuthn',
            },
        ),
    ] 