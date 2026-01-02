from rest_framework import serializers
from .models import Notification
from users.serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    recipient_details = UserSerializer(source='recipient', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
