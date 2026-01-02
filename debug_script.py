
import sys
import os
import django
from django.conf import settings

from gym.models import Notification, MemberAchievement, Member, Trainer
from gym.serializers import NotificationSerializer, MemberAchievementSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

print("--- CREATING TEST DATA ---")
try:
    # Get or create user
    user, created = User.objects.get_or_create(email='test@example.com', defaults={'username': 'testuser'})
    if created:
        user.set_password('pass')
        user.save()
    
    trainer_user, _ = User.objects.get_or_create(email='trainer@example.com', defaults={'username': 'traineruser', 'role': 'trainer'})
    
    member, _ = Member.objects.get_or_create(user=user, defaults={'date_of_birth': '2000-01-01', 'gender': 'M', 'address': '123 St', 'join_date': timezone.now().date()})
    
    # Create Notification
    notif = Notification.objects.create(
        recipient=user,
        title="Test Notif",
        message="Test Message",
        read=False,
        # created_at handled by auto_now_add
    )
    print(f"Created Notification: {notif.id}")
    
    # Create Achievement
    ach = MemberAchievement.objects.create(
        member=member,
        achievement_slug="beginner_gains",
        awarded_by=trainer_user
    )
    print(f"Created Achievement: {ach.id}")

    print("--- DEBUGGING NOTIFICATIONS ---")
    serializer = NotificationSerializer([notif], many=True)
    print("Notification Serialization success!")
    print(serializer.data)

    print("\n--- DEBUGGING ACHIEVEMENTS ---")
    ach_serializer = MemberAchievementSerializer([ach], many=True)
    print("Achievement Serialization success!")
    print(ach_serializer.data)

except Exception as e:
    print(f"CRITICAL ERROR in Test: {e}")
    import traceback
    traceback.print_exc()
