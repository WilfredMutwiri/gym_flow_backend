from django.db import models
from shared.basemodel import BaseModel

class Session(BaseModel):
    trainer = models.ForeignKey('core.Trainer', on_delete=models.CASCADE, related_name='scheduled_sessions')
    member = models.ForeignKey('core.Member', on_delete=models.CASCADE, related_name='booked_sessions')
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, default='pending', db_index=True) # pending, confirmed, cancelled, completed
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Session: {self.member.user.get_full_name()} with {self.trainer.user.get_full_name()}"
