import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from gym.models import Member, Trainer

User = get_user_model()

def create_users():
    # Admin
    if not User.objects.filter(email='admin@fithub.com').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@fithub.com',
            password='admin123',
            first_name='Ad',
            last_name='Min',
            role='admin'
        )
        print("Created Admin")

    # Trainer
    if not User.objects.filter(email='trainer@fithub.com').exists():
        trainer_user = User.objects.create_user(
            username='trainer',
            email='trainer@fithub.com',
            password='trainer123',
            first_name='Sarah',
            last_name='Trainer',
            role='trainer'
        )
        Trainer.objects.create(
            user=trainer_user,
            hire_date='2024-01-01',
            specializations=['HIIT', 'Yoga']
        )
        print("Created Trainer")

    # Member
    if not User.objects.filter(email='member@fithub.com').exists():
        member_user = User.objects.create_user(
            username='member',
            email='member@fithub.com',
            password='member123',
            first_name='John',
            last_name='Member',
            role='member'
        )
        Member.objects.create(
            user=member_user,
            date_of_birth='1990-01-01',
            gender='male',
            address='123 Gym St',
            join_date='2024-01-01'
        )
        print("Created Member")

if __name__ == "__main__":
    create_users()
