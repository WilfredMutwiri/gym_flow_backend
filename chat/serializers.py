from rest_framework import serializers
from .models import Conversation, ChatMessage, Message
from core.serializers import MemberSerializer, TrainerSerializer
from users.serializers import UserSerializer

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = '__all__'
    
    def get_sender_name(self, obj):
        return obj.sender.get_full_name()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_deleted:
            data['content'] = "This message was deleted"
        return data

class ConversationSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    trainer_details = TrainerSerializer(source='trainer', read_only=True)
    member_name = serializers.SerializerMethodField()
    trainer_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = '__all__'
    
    def get_member_name(self, obj):
        return obj.member.user.get_full_name() if obj.member else "Gym Support"
        
    def get_trainer_name(self, obj):
        return obj.trainer.user.get_full_name() if obj.trainer else "Gym Support"

    def get_last_message(self, obj):
        last_msg = obj.chat_messages.order_by('-sent_at').first()
        if last_msg:
            return {
                'content': last_msg.content,
                'sent_at': last_msg.sent_at,
                'sender_name': last_msg.sender.get_full_name()
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.chat_messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

class MessageSerializer(serializers.ModelSerializer):
    recipient_details = MemberSerializer(source='recipient', read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
