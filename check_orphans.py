import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from gym.models import Member, Trainer

User = get_user_model()

def check_orphans():
    print("--- Users ---")
    users = User.objects.all()
    for u in users:
        has_member = hasattr(u, 'member_profile')
        has_trainer = hasattr(u, 'trainer_profile')
        print(f"User: {u.email} (ID: {u.id}, Role: {u.role}) | Member: {has_member} | Trainer: {has_trainer}")

    print("\n--- Members ---")
    members = Member.objects.all()
    for m in members:
        print(f"Member: {m.id} | User: {m.user.email}")

if __name__ == "__main__":
    check_orphans()
