from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .utils import send_notification_email
import threading

@receiver(post_save, sender=Notification)
def send_email_on_notification_create(sender, instance, created, **kwargs):
    if created and not instance.email_sent:
        # Send email in a separate thread to avoid blocking the response
        email_thread = threading.Thread(target=send_notification_email, args=(instance,))
        email_thread.start()
