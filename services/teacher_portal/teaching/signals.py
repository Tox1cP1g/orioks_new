from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Grade, StudentSubmission

@receiver(post_save, sender=Grade)
def notify_student_about_grade(sender, instance, created, **kwargs):
    """
    Отправляет уведомление студенту при выставлении оценки
    """
    if created:
        # TODO: Реализовать отправку уведомления через API сервиса уведомлений
        pass

@receiver(post_save, sender=StudentSubmission)
def notify_teachers_about_submission(sender, instance, created, **kwargs):
    """
    Уведомляет преподавателей о новом решении
    """
    if created:
        # TODO: Реализовать отправку уведомления через API сервиса уведомлений
        pass

@receiver(post_save, sender=Grade)
def update_submission_status(sender, instance, created, **kwargs):
    """
    Обновляет статус решения при выставлении оценки
    """
    if created:
        submission = instance.submission
        submission.status = 'COMPLETED'
        submission.save(update_fields=['status']) 