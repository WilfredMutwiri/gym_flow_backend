from rest_framework import serializers
from .models import Session
from core.serializers import MemberSerializer, TrainerSerializer

class SessionSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    trainer_details = TrainerSerializer(source='trainer', read_only=True)
    
    class Meta:
        model = Session
        fields = '__all__'
