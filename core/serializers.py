from rest_framework import serializers
from .models import Trainer, Member, GymSetting
from users.serializers import UserSerializer

class TrainerSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Trainer
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    active_plan = serializers.SerializerMethodField()
    assigned_trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=Trainer.objects.all(), 
        source='assigned_trainer', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Member
        fields = '__all__'

    def get_active_plan(self, obj):
        # We'll use string-based check or import from subscriptions if needed
        # For now, to avoid circular imports, we check via reverse relation
        active_sub = obj.subscriptions.filter(status='active').first()
        if active_sub and active_sub.plan:
            return active_sub.plan.name
        return "No Active Plan"

class GymSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymSetting
        fields = '__all__'
