from django.urls import path
from .views import (
    ConversationListView, ConversationDetailView, MessageListView, MemberListForChatView
)

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('messages/', MessageListView.as_view(), name='message-list'),
    path('members/', MemberListForChatView.as_view(), name='chat-members'),
]
