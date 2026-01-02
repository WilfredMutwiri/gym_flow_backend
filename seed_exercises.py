import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gym.models import Exercise

exercises = [
    {"name": "Bench Press", "description": "Chest exercise", "muscle_group": "Chest", "equipment": "Barbell"},
    {"name": "Squat", "description": "Leg exercise", "muscle_group": "Legs", "equipment": "Barbell"},
    {"name": "Deadlift", "description": "Back exercise", "muscle_group": "Back", "equipment": "Barbell"},
    {"name": "Overhead Press", "description": "Shoulder exercise", "muscle_group": "Shoulder", "equipment": "Barbell"},
    {"name": "Pull Up", "description": "Back exercise", "muscle_group": "Back", "equipment": "Bodyweight"},
]

for ex in exercises:
    obj, created = Exercise.objects.get_or_create(
        name=ex['name'],
        defaults=ex
    )
    if created:
        print(f"Created exercise: {obj.name}")
    else:
        print(f"Exercise already exists: {obj.name}")
