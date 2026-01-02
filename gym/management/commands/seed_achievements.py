from django.core.management.base import BaseCommand
from gym.models import Achievement

class Command(BaseCommand):
    help = 'Seeds initial achievements'

    def handle(self, *args, **kwargs):
        achievements = [
            {
                'name': 'Weight Loss Warrior',
                'description': 'Awarded for significant progress in weight loss.',
                'icon_name': 'scale'
            },
            {
                'name': 'Consistency King',
                'description': 'Awarded for maintaining a workout streak of 7+ days.',
                'icon_name': 'calendar'
            },
            {
                'name': 'Strength Master',
                'description': 'Awarded for hitting a new personal record in lifting.',
                'icon_name': 'dumbbell'
            },
            {
                'name': 'Early Bird',
                'description': 'Awarded for completing 5 morning workouts in a row.',
                'icon_name': 'sun'
            },
            {
                'name': 'Night Owl',
                'description': 'Awarded for late night gym sessions.',
                'icon_name': 'moon'
            },
            {
                'name': 'Program Finisher',
                'description': 'Awarded for completing a full workout program.',
                'icon_name': 'trophy'
            }
        ]

        for ach_data in achievements:
            obj, created = Achievement.objects.get_or_create(
                name=ach_data['name'],
                defaults=ach_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created achievement: {obj.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Achievement already exists: {obj.name}'))
