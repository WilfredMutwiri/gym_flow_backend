from django.db import models
from django.conf import settings
from shared.basemodel import BaseModel

class Conversation(BaseModel):
    """Represents a chat conversation between admin and a member"""
    member = models.ForeignKey('core.Member', on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    trainer = models.ForeignKey('core.Trainer', on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    last_message_at = models.DateTimeField(auto_now=True)
    deleted_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='deleted_conversations')
    
    class Meta:
        ordering = ['-last_message_at']
    
    def __str__(self):
        if self.member and self.trainer:
            return f"Conversation: {self.member.user.get_full_name()} <-> {self.trainer.user.get_full_name()}"
        if self.member:
            return f"Conversation with Member: {self.member.user.get_full_name()}"
        if self.trainer:
            return f"Conversation with Trainer: {self.trainer.user.get_full_name()}"
        return f"Support Conversation {self.id}"

class ChatMessage(BaseModel):
    """Individual messages in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages_sent')
    content = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['sent_at']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} at {self.sent_at}"

class Message(BaseModel):
    recipient = models.ForeignKey('core.Member', on_delete=models.CASCADE, related_name='messages')
    type = models.CharField(max_length=50)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    channel = models.CharField(max_length=20) # email, sms
    status = models.CharField(max_length=20, db_index=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
