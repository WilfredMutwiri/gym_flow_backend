from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.permissions import IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_not_found,
)

class NotificationListView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(tags=['Notifications'], operation_summary='List my notifications')
    def get(self, request):
        try:
            notifications = Notification.objects.filter(recipient=request.user)
            serializer = NotificationSerializer(notifications, many=True)
            return handle_success(data=serializer.data, message="Notifications retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to fetch notifications: {str(e)}")

    @swagger_auto_schema(tags=['Notifications'], operation_summary='Mark notification as read')
    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.read = True
            notification.save()
            return handle_success(message="Notification marked as read")
        except Notification.DoesNotExist:
            return handle_not_found(message="Notification not found")

    @swagger_auto_schema(tags=['Notifications'], operation_summary='Delete notification')
    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.delete()
            return handle_success(message="Notification deleted successfully")
        except Notification.DoesNotExist:
            return handle_not_found(message="Notification not found")
