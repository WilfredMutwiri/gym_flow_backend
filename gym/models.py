from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from shared.basemodel import BaseModel

class Trainer(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trainer_profile')
    specializations = models.JSONField(default=list)  # List of strings
    bio = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    hire_date = models.DateField()

    def __str__(self):
        return f"Trainer: {self.user.email}"

class Member(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='member_profile')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    emergency_contact = models.JSONField(default=dict)  # {name, phone, relationship}
    status = models.CharField(max_length=20, default='active')
    join_date = models.DateField()
    assigned_trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Member: {self.user.email}"

class AttendanceRecord(BaseModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendance')
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField()
    method = models.CharField(max_length=20)  # manual, qr, id

class Program(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20)  # beginner, intermediate, advanced
    goal = models.CharField(max_length=200)
    created_by = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, related_name='created_programs')
    assigned_members = models.ManyToManyField(Member, related_name='assigned_programs', blank=True)
    status = models.CharField(max_length=20, default='active')
    version = models.IntegerField(default=1)

    def __str__(self):
        return self.name

class WorkoutDay(BaseModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='workout_days')
    day_number = models.IntegerField()
    name = models.CharField(max_length=100)

class Exercise(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    muscle_group = models.CharField(max_length=100)
    equipment = models.CharField(max_length=100, blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class WorkoutSet(BaseModel):
    workout_day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.IntegerField()
    reps = models.CharField(max_length=50)
    weight = models.FloatField(null=True, blank=True)
    rest = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    safety_notes = models.TextField(blank=True, null=True)

class SubscriptionPlan(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField()  # in days
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return self.name

class MemberSubscription(BaseModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20)  # active, expired, cancelled
    payment_status = models.CharField(max_length=20) # paid, pending, overdue
    amount = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(BaseModel):
    subscription = models.ForeignKey(MemberSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)  # cash, card, etc
    status = models.CharField(max_length=20)  # completed, pending, failed
    transaction_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)

class ProgressEntry(BaseModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='progress_entries')
    date = models.DateField()
    weight = models.FloatField(null=True, blank=True)
    body_fat = models.FloatField(null=True, blank=True)
    measurements = models.JSONField(default=dict)
    photos = models.JSONField(default=list)
    notes = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class Message(BaseModel):
    recipient = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='messages')
    type = models.CharField(max_length=50)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    channel = models.CharField(max_length=20) # email, sms
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')

class Conversation(BaseModel):
    """Represents a chat conversation between admin and a member"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='conversations')
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    last_message_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
    
    def __str__(self):
        if self.trainer:
            return f"Conversation: {self.member.user.get_full_name()} <-> {self.trainer.user.get_full_name()}"
        return f"Conversation with {self.member.user.get_full_name()}"

class ChatMessage(BaseModel):
    """Individual messages in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages_sent')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sent_at']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} at {self.sent_at}"

class Session(BaseModel):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='scheduled_sessions')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='booked_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, default='pending') # pending, confirmed, cancelled, completed
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Session: {self.member.user.get_full_name()} with {self.trainer.user.get_full_name()}"

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

class Achievement(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField()
    icon_name = models.CharField(max_length=100) # For frontend icon mapping
    
    def __str__(self):
        return self.name

class MemberAchievement(BaseModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.member} - {self.achievement}"
