from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import Conversation, ChatMessage, Member
from .serializers import ConversationSerializer, ChatMessageSerializer
from .permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)

class ConversationListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Chat'], operation_summary='List all conversations')
    def get(self, request):
        """Get all conversations for the current user"""
        user = request.user
        
        if user.role == 'admin':
            # Admin sees all conversations
            conversations = Conversation.objects.all()
        elif user.role == 'member':
            # Members see only their conversations
            try:
                member = Member.objects.get(user=user)
                conversations = Conversation.objects.filter(member=member)
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
        
        serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        return handle_success(data=serializer.data, message="Conversations retrieved successfully")

    @swagger_auto_schema(tags=['Chat'], operation_summary='Create or get conversation')
    def post(self, request):
        """Create a new conversation or get existing one"""
        member_id = request.data.get('member_id')
        
        if not member_id:
            return handle_validation_error(errors={'member_id': 'This field is required'})
        
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return handle_not_found(message="Member not found")
        
        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(member=member)
        serializer = ConversationSerializer(conversation, context={'request': request})
        
        message = "Conversation created successfully" if created else "Conversation retrieved successfully"
        return handle_success(data=serializer.data, message=message, status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ConversationDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Chat'], operation_summary='Get conversation messages')
    def get(self, request, conversation_id):
        """Get all messages in a conversation"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return handle_not_found(message="Conversation not found")
        
        # Check permissions
        user = request.user
        if user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                if conversation.member != member:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Mark messages as read
        conversation.chat_messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        
        messages = conversation.chat_messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return handle_success(data=serializer.data, message="Messages retrieved successfully")

    @swagger_auto_schema(tags=['Chat'], operation_summary='Send a message')
    def post(self, request, conversation_id):
        """Send a message in a conversation"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return handle_not_found(message="Conversation not found")
        
        content = request.data.get('content')
        if not content:
            return handle_validation_error(errors={'content': 'Message content is required'})
        
        # Check permissions
        user = request.user
        if user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                if conversation.member != member:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Create message
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )
        
        # Update conversation's last_message_at
        conversation.save()  # This triggers auto_now on last_message_at
        
        serializer = ChatMessageSerializer(message)
        return handle_success(data=serializer.data, message="Message sent successfully", status_code=status.HTTP_201_CREATED)


class MemberListForChatView(views.APIView):
    """Get list of all members for starting conversations"""
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Chat'], operation_summary='List members for chat')
    def get(self, request):
        from .serializers import MemberSerializer
        members = Member.objects.filter(status='active')
        serializer = MemberSerializer(members, many=True)
        return handle_success(data=serializer.data, message="Members retrieved successfully")
