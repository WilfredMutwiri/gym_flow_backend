from rest_framework import serializers
from .models import AttendanceRecord
from core.serializers import MemberSerializer

class AttendanceRecordSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
