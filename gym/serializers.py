from rest_framework import serializers
from .models import (
    Trainer, Member, AttendanceRecord, Program, WorkoutDay, Exercise, 
    WorkoutSet, SubscriptionPlan, MemberSubscription, Payment, 
    ProgressEntry, Message, GymSetting, Conversation, ChatMessage
)
from users.serializers import UserSerializer

class TrainerSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Trainer
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    active_plan = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = '__all__'

    def get_active_plan(self, obj):
        active_sub = obj.subscriptions.filter(status='active').first()
        if active_sub and active_sub.plan:
            return active_sub.plan.name
        return "No Active Plan"

class AttendanceRecordSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    
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
    created_by_details = TrainerSerializer(source='created_by', read_only=True)
    assigned_members = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
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
    subscription_details = MemberSubscriptionSerializer(source='subscription', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'

class ProgressEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressEntry
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    recipient_details = MemberSerializer(source='recipient', read_only=True)
    sender_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'

class GymSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymSetting
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = '__all__'
    
    def get_sender_name(self, obj):
        return obj.sender.get_full_name()

class ConversationSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    member_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = '__all__'
    
    def get_member_name(self, obj):
        return obj.member.user.get_full_name()
    
    def get_last_message(self, obj):
        last_msg = obj.chat_messages.last()
        if last_msg:
            return {
                'content': last_msg.content,
                'sent_at': last_msg.sent_at,
                'sender_name': last_msg.sender.get_full_name()
            }
        return None
    
    def get_unread_count(self, obj):
        # Count unread messages not sent by current user
        request = self.context.get('request')
        if request and request.user:
            return obj.chat_messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
