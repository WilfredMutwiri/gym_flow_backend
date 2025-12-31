from rest_framework import serializers
from .models import (
    Trainer, Member, AttendanceRecord, Program, WorkoutDay, Exercise, 
    WorkoutSet, SubscriptionPlan, MemberSubscription, Payment, 
    ProgressEntry, Message
)
from users.serializers import UserSerializer

class TrainerSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Trainer
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Member
        fields = '__all__'

class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'

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
    
    class Meta:
        model = Program
        fields = '__all__'

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class MemberSubscriptionSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)

    class Meta:
        model = MemberSubscription
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class ProgressEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressEntry
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
