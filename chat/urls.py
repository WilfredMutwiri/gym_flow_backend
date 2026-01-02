from django.urls import path
from .views import ConversationListView, ConversationDetailView, MemberListForChatView, MessageListView, ChatMessageDeleteView

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('messages/<int:message_id>/delete/', ChatMessageDeleteView.as_view(), name='message-delete'),
    path('members/', MemberListForChatView.as_view(), name='chat-member-list'),
    path('list/', MessageListView.as_view(), name='message-list-all'),
]
