from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import Conversation, ChatMessage, Member, Trainer, Notification
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
            # Admins see everything
            conversations = Conversation.objects.all()
        elif user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                # Member sees convos where they are participant (trainer-member or admin-member)
                conversations = Conversation.objects.filter(member=member)
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
        elif user.role == 'trainer':
             try:
                trainer = Trainer.objects.get(user=user)
                # Trainer sees convos where they are participant (trainer-member or admin-trainer)
                conversations = Conversation.objects.filter(trainer=trainer)
             except Trainer.DoesNotExist:
                return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
        
        serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        return handle_success(data=serializer.data, message="Conversations retrieved successfully")

    @swagger_auto_schema(tags=['Chat'], operation_summary='Create or get conversation')
    def post(self, request):
        """Create a new conversation or get existing one"""
        member_id = request.data.get('member_id')
        trainer_id = request.data.get('trainer_id')
        
        member = None
        trainer = None

        # Resolve member if provided
        if member_id:
            try:
                member = Member.objects.get(id=member_id)
            except Member.DoesNotExist:
                return handle_not_found(message="Member not found")
        
        # Resolve trainer if provided
        if trainer_id:
            try:
                trainer = Trainer.objects.get(id=trainer_id)
            except Trainer.DoesNotExist:
                return handle_not_found(message="Trainer not found")

        # Determine participants based on user role and input
        if request.user.role == 'member':
            try:
                current_member = Member.objects.get(user=request.user)
                # If member starts a chat, they must be the member participant
                member = current_member
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found")
        
        elif request.user.role == 'trainer':
            try:
                current_trainer = Trainer.objects.get(user=request.user)
                # If trainer starts a chat, they must be the trainer participant
                trainer = current_trainer
            except Trainer.DoesNotExist:
                 return handle_error(message="Trainer profile not found")

        # Validation: At least one participant must be defined (Admin support chat has only one participant)
        if not member and not trainer:
            return handle_validation_error(errors={'participants': 'At least one participant (member or trainer) is required'})

        # Get or create conversation (Note: if both are null/missing for a role, it implies admin support if role allows)
        conversation, created = Conversation.objects.get_or_create(member=member, trainer=trainer)
            
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
        if user.role == 'admin':
            pass # Admin can see all
        elif user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                if conversation.member != member:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
        elif user.role == 'trainer':
            try:
                trainer = Trainer.objects.get(user=user)
                if conversation.trainer != trainer:
                     return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Trainer.DoesNotExist:
                return handle_error(message="Trainer profile not found")
        
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
        if user.role == 'admin':
            pass
        elif user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                if conversation.member != member:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
        elif user.role == 'trainer':
            try:
                trainer = Trainer.objects.get(user=user)
                if conversation.trainer != trainer:
                      return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Trainer.DoesNotExist:
                 return handle_error(message="Trainer profile not found")
        
        # Create message
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )
        
        # Create Notification for the recipient
        recipient = None
        if user.role == 'member':
            if conversation.trainer:
                recipient = conversation.trainer.user
            else:
                # Support chat - notify all admins
                from django.contrib.auth import get_user_model
                User = get_user_model()
                admins = User.objects.filter(role='admin')
                for admin in admins:
                    Notification.objects.create(
                        recipient=admin,
                        title=f"New Support Message from {user.get_full_name()}",
                        message=content[:100] + ("..." if len(content) > 100 else "")
                    )
        elif user.role == 'trainer':
            if conversation.member:
                recipient = conversation.member.user
            else:
                # Support chat - notify all admins
                from django.contrib.auth import get_user_model
                User = get_user_model()
                admins = User.objects.filter(role='admin')
                for admin in admins:
                     Notification.objects.create(
                        recipient=admin,
                        title=f"New Staff Message from {user.get_full_name()}",
                        message=content[:100] + ("..." if len(content) > 100 else "")
                    )
        elif user.role == 'admin':
            # If it's a trainer chat or member chat, notify the relevant party
             if conversation.trainer:
                 recipient = conversation.trainer.user
             elif conversation.member:
                 recipient = conversation.member.user
        
        if recipient:
            Notification.objects.create(
                recipient=recipient,
                title=f"New Message from {user.get_full_name()}",
                message=content[:100] + ("..." if len(content) > 100 else "")
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
