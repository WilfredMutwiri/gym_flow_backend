from django.db import models
from django.conf import settings
from shared.basemodel import BaseModel

class Trainer(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trainer_profile')
    specializations = models.JSONField(default=list)  # List of strings
    bio = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='active', db_index=True)
    hire_date = models.DateField()

    def __str__(self):
        return f"Trainer: {self.user.email}"

class Member(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='member_profile')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    emergency_contact = models.JSONField(default=dict)  # {name, phone, relationship}
    status = models.CharField(max_length=20, default='active', db_index=True)
    join_date = models.DateField()
    assigned_trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Member: {self.user.email}"

class GymSetting(BaseModel):
    gym_name = models.CharField(max_length=200, default='Gym Flow')
    address = models.TextField(default='123 Fitness Blvd, Workout City')
    phone = models.CharField(max_length=20, default='+1 234 567 8900')
    email = models.EmailField(default='contact@gymflow.com')
    
    # Notifications
    notify_new_member = models.BooleanField(default=True)
    notify_payment_alerts = models.BooleanField(default=True)
    notify_maintenance = models.BooleanField(default=False)

    def __str__(self):
        return self.gym_name
