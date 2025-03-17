from django.apps import AppConfig


class TeachingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'teaching'
    verbose_name = 'Портал преподавателей'

    def ready(self):
        import teaching.signals
