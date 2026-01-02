from django.db import models
from shared.basemodel import BaseModel

class Program(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20)  # beginner, intermediate, advanced
    goal = models.CharField(max_length=200)
    created_by = models.ForeignKey('core.Trainer', on_delete=models.SET_NULL, null=True, related_name='created_programs')
    assigned_members = models.ManyToManyField('core.Member', related_name='assigned_programs', blank=True)
    status = models.CharField(max_length=20, default='active', db_index=True)
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
