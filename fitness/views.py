from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import ProgressEntry, MemberAchievement
from .serializers import ProgressEntrySerializer, MemberAchievementSerializer
from core.models import Member, Trainer
from notifications.models import Notification
from rest_framework.permissions import IsAuthenticated
from shared.permissions import IsMember
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)

class ProgressEntryListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Progress'], operation_summary='List progress entries')
    def get(self, request, member_id=None):
        mid = member_id or request.query_params.get('member')
        if mid:
            entries = ProgressEntry.objects.filter(member_id=mid).select_related('member__user', 'recorded_by')
        else:
            entries = ProgressEntry.objects.select_related('member__user', 'recorded_by').all()
        serializer = ProgressEntrySerializer(entries, many=True)
        return handle_success(data=serializer.data, message="Progress entries retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Progress'], operation_summary='Record progress', request_body=ProgressEntrySerializer)
    def post(self, request, member_id=None):
        data = request.data.copy()
        if member_id and 'member' not in data:
            data['member'] = member_id
            
        serializer = ProgressEntrySerializer(data=data)
        if serializer.is_valid():
            entry = serializer.save(recorded_by=request.user)
            if request.user.role == 'trainer' or request.user.role == 'admin':
                Notification.objects.create(
                    recipient=entry.member.user,
                    title="Progress Updated",
                    message=f"Your trainer/admin {request.user.get_full_name()} has updated your progress records."
                )
            return handle_success(data=serializer.data, message="Progress entry recorded successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class MemberAchievementView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(tags=['Achievements'], operation_summary='List member achievements')
    def get(self, request, member_id=None):
        if not member_id:
            member_id = request.query_params.get('member_id')
        if not member_id:
             if request.user.role == 'member':
                 try:
                    member = Member.objects.get(user=request.user)
                    member_id = member.id
                 except Member.DoesNotExist:
                     return handle_error(message="Member profile not found")
             else:
                 return handle_error(message="Member ID required")
        try:
            achievements = MemberAchievement.objects.filter(member_id=member_id).select_related('member__user', 'awarded_by')
            serializer = MemberAchievementSerializer(achievements, many=True)
            return handle_success(data=serializer.data, message="Member achievements retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to fetch achievements: {str(e)}")

    @swagger_auto_schema(
        tags=['Achievements'], 
        operation_summary='Award achievement to member',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'member_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'achievement_slug': openapi.Schema(type=openapi.TYPE_STRING),
                'note': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['member_id', 'achievement_slug']
        )
    )
    def post(self, request):
        try:
            member_id = request.data.get('member_id')
            achievement_slug = request.data.get('achievement_slug')
            note = request.data.get('note', '')
            if not member_id or not achievement_slug:
                return handle_error(message="Member ID and Achievement Slug are required", status_code=400)
            if MemberAchievement.objects.filter(member_id=member_id, achievement_slug=achievement_slug).exists():
                 return handle_error(message="Member already has this achievement")
            
            MemberAchievement.objects.create(
                member_id=member_id,
                achievement_slug=achievement_slug,
                awarded_by=request.user,
                note=note
            )
            
            try:
                member = Member.objects.get(id=member_id)
                Notification.objects.create(
                    recipient=member.user,
                    title="New Achievement Unlocked!",
                    message=f"You have been awarded a new badge! Check your progress page.",
                )
            except Member.DoesNotExist:
                 return handle_error(message="Member not found")

            return handle_success(message="Achievement awarded successfully")
        except Exception as e:
             return handle_error(message=f"Failed to award achievement: {str(e)}")
