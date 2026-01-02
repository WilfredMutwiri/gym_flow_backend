from django.db import models
from django.conf import settings
from shared.basemodel import BaseModel

class ProgressEntry(BaseModel):
    member = models.ForeignKey('core.Member', on_delete=models.CASCADE, related_name='progress_entries')
    date = models.DateField(db_index=True)
    weight = models.FloatField(null=True, blank=True)
    body_fat = models.FloatField(null=True, blank=True)
    measurements = models.JSONField(default=dict)
    photos = models.JSONField(default=list)
    notes = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class MemberAchievement(BaseModel):
    member = models.ForeignKey('core.Member', on_delete=models.CASCADE, related_name='achievements')
    achievement_slug = models.CharField(max_length=100, db_index=True) # Stores the ID from frontend JSON
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.member} - {self.achievement_slug}"
