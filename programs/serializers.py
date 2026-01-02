from rest_framework import serializers
from .models import Program, WorkoutDay, Exercise, WorkoutSet
from core.serializers import MemberSerializer, TrainerSerializer

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise_details = ExerciseSerializer(source='exercise', read_only=True)
    
    class Meta:
        model = WorkoutSet
        fields = '__all__'

class WorkoutDaySerializer(serializers.ModelSerializer):
    exercises = WorkoutSetSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkoutDay
        fields = '__all__'

class ProgramSerializer(serializers.ModelSerializer):
    workout_days = WorkoutDaySerializer(many=True, read_only=True)
    assigned_members_details = MemberSerializer(source='assigned_members', many=True, read_only=True)
    created_by_details = TrainerSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = Program
        fields = '__all__'
