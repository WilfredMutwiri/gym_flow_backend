from django.db import models
from django.conf import settings
from shared.basemodel import BaseModel

class Notification(BaseModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False, db_index=True)
    email_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient}: {self.title}"
