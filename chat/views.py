from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import Conversation, ChatMessage, Message
from .serializers import ConversationSerializer, ChatMessageSerializer, MessageSerializer
from core.models import Member, Trainer
from core.serializers import MemberSerializer
from shared.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)
from notifications.models import Notification
from django.db.models import Q

class ConversationListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Chat'], operation_summary='List all conversations')
    def get(self, request):
        user = request.user
        if user.role == 'admin':
            conversations = Conversation.objects.filter(Q(member__isnull=True) | Q(trainer__isnull=True)).exclude(deleted_by=user).select_related('member__user', 'trainer__user').prefetch_related('chat_messages__sender')
        elif user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                conversations = Conversation.objects.filter(member=member).exclude(deleted_by=user).select_related('member__user', 'trainer__user').prefetch_related('chat_messages__sender')
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
        elif user.role == 'trainer':
             try:
                trainer = Trainer.objects.get(user=user)
                conversations = Conversation.objects.filter(trainer=trainer).exclude(deleted_by=user).select_related('member__user', 'trainer__user').prefetch_related('chat_messages__sender')
             except Trainer.DoesNotExist:
                return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
        
        serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        return handle_success(data=serializer.data, message="Conversations retrieved successfully")

    @swagger_auto_schema(tags=['Chat'], operation_summary='Create or get conversation')
    def post(self, request):
        member_id = request.data.get('member_id')
        trainer_id = request.data.get('trainer_id')
        member = None
        trainer = None

        if member_id:
            try:
                member = Member.objects.get(id=member_id)
            except Member.DoesNotExist:
                return handle_not_found(message="Member not found")
        if trainer_id:
            try:
                trainer = Trainer.objects.get(id=trainer_id)
            except Trainer.DoesNotExist:
                return handle_not_found(message="Trainer not found")

        if request.user.role == 'member':
            try:
                current_member = Member.objects.get(user=request.user)
                member = current_member
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found")
        elif request.user.role == 'trainer':
            try:
                current_trainer = Trainer.objects.get(user=request.user)
                trainer = current_trainer
            except Trainer.DoesNotExist:
                 return handle_error(message="Trainer profile not found")

        if not member and not trainer:
            return handle_validation_error(errors={'participants': 'At least one participant is required'})

        conversation, created = Conversation.objects.get_or_create(member=member, trainer=trainer)
        
        # If the conversation was previously deleted by this user, restore it
        if request.user in conversation.deleted_by.all():
            conversation.deleted_by.remove(request.user)
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        message = "Conversation created successfully" if created else "Conversation retrieved successfully"
        return handle_success(data=serializer.data, message=message, status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ConversationDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Chat'], operation_summary='Get conversation messages')
    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return handle_not_found(message="Conversation not found")
        
        user = request.user
        if user.role == 'admin':
            pass
        elif user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                if conversation.member != member:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return handle_not_found(message="Member profile not found")
        elif user.role == 'trainer':
            try:
                trainer = Trainer.objects.get(user=user)
                if conversation.trainer != trainer:
                      return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Trainer.DoesNotExist:
                return handle_not_found(message="Trainer profile not found")
        
        conversation.chat_messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        messages = conversation.chat_messages.select_related('sender').all()
        serializer = ChatMessageSerializer(messages, many=True)
        return handle_success(data=serializer.data, message="Messages retrieved successfully")

    @swagger_auto_schema(tags=['Chat'], operation_summary='Send a message')
    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return handle_not_found(message="Conversation not found")
        
        content = request.data.get('content')
        if not content:
            return handle_validation_error(errors={'content': 'Message content is required'})
        
        user = request.user
        if user.role == 'admin':
            pass
        elif user.role == 'member':
            try:
                member = Member.objects.get(user=user)
                if conversation.member != member:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return handle_not_found(message="Member profile not found")
        elif user.role == 'trainer':
            try:
                trainer = Trainer.objects.get(user=user)
                if conversation.trainer != trainer:
                      return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            except Trainer.DoesNotExist:
                 return handle_not_found(message="Trainer profile not found")
        
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )
        
        recipient = None
        if user.role == 'member':
            if conversation.trainer:
                recipient = conversation.trainer.user
            else:
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
        
        conversation.save()
        serializer = ChatMessageSerializer(message)
        return handle_success(data=serializer.data, message="Message sent successfully", status_code=status.HTTP_201_CREATED)

    @swagger_auto_schema(tags=['Chat'], operation_summary='Delete conversation for current user')
    def delete(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return handle_not_found(message="Conversation not found")
        
        conversation.deleted_by.add(request.user)
        return handle_success(message="Conversation deleted for you")

class ChatMessageDeleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Chat'], operation_summary='Delete a message for everyone')
    def delete(self, request, message_id):
        try:
            message = ChatMessage.objects.get(id=message_id)
        except ChatMessage.DoesNotExist:
            return handle_not_found(message="Message not found")
        
        if message.sender != request.user and request.user.role != 'admin':
            return handle_error(message="Unauthorized to delete this message", status_code=status.HTTP_403_FORBIDDEN)
        
        message.is_deleted = True
        message.save()
        return handle_success(message="Message deleted for everyone")

class MemberListForChatView(views.APIView):
    """Get list of all members for starting conversations"""
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Chat'], operation_summary='List members for chat')
    def get(self, request):
        members = Member.objects.filter(status='active')
        serializer = MemberSerializer(members, many=True)
        return handle_success(data=serializer.data, message="Members retrieved successfully")

class MessageListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Messages'], operation_summary='List messages')
    def get(self, request):
        user = request.user
        if user.role == 'member':
            messages = Message.objects.filter(recipient__user=user)
        else:
            messages = Message.objects.all()
        serializer = MessageSerializer(messages, many=True)
        return handle_success(data=serializer.data, message="Messages retrieved successfully", status_code=status.HTTP_200_OK)
