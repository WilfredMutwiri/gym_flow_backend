from rest_framework import serializers
from .models import ProgressEntry, MemberAchievement
from core.serializers import MemberSerializer
from users.serializers import UserSerializer

class ProgressEntrySerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    recorded_by_details = UserSerializer(source='recorded_by', read_only=True)
    
    class Meta:
        model = ProgressEntry
        fields = '__all__'

class MemberAchievementSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    awarded_by_details = UserSerializer(source='awarded_by', read_only=True)
    awarded_by_name = serializers.SerializerMethodField()
    
    def get_awarded_by_name(self, obj):
        if obj.awarded_by:
            return obj.awarded_by.get_full_name()
        return "System"
    
    class Meta:
        model = MemberAchievement
        fields = '__all__'
