from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .serializers import TrainerSerializer, MemberSerializer, GymSettingSerializer
from .models import Trainer, Member, GymSetting
from shared.permissions import IsAdminUser, IsAdminOrTrainer, IsTrainer, IsMember
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)
from notifications.models import Notification

class TrainerListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Trainers'],
        operation_summary='List all trainers',
        responses={200: TrainerSerializer(many=True)}
    )
    def get(self, request):
        trainers = Trainer.objects.select_related('user').all()
        serializer = TrainerSerializer(trainers, many=True)
        return handle_success(data=serializer.data, message="Trainers retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['Trainers'],
        operation_summary='Create a new trainer',
        request_body=TrainerSerializer,
        responses={201: TrainerSerializer()}
    )
    def post(self, request):
        if request.user.role != 'admin':
            return handle_error(message="You do not have permission to perform this action.", status_code=status.HTTP_403_FORBIDDEN)
            
        serializer = TrainerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Trainer created successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class TrainerDetailView(views.APIView):
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Trainer.objects.get(pk=pk)
        except Trainer.DoesNotExist:
            return None

    @swagger_auto_schema(tags=['Trainers'], operation_summary='Get trainer details')
    def get(self, request, pk):
        trainer = self.get_object(pk)
        if not trainer:
            return handle_not_found(message="Trainer not found")
        serializer = TrainerSerializer(trainer)
        return handle_success(data=serializer.data, message="Trainer details retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Trainers'], operation_summary='Update trainer')
    def put(self, request, pk):
        trainer = self.get_object(pk)
        if not trainer:
            return handle_not_found(message="Trainer not found")
        serializer = TrainerSerializer(trainer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Trainer updated successfully", status_code=status.HTTP_200_OK)
        return handle_validation_error(errors=serializer.errors)

    def patch(self, request, pk):
        return self.put(request, pk)

    @swagger_auto_schema(tags=['Trainers'], operation_summary='Delete trainer')
    def delete(self, request, pk):
        trainer = self.get_object(pk)
        if not trainer:
            return handle_not_found(message="Trainer not found")
        
        from django.db import transaction
        try:
            with transaction.atomic():
                user = trainer.user
                user.delete() # This will cascade delete the trainer profile
            return handle_success(message="Trainer and associated user deleted successfully", status_code=status.HTTP_200_OK)
        except Exception as e:
            return handle_error(message=f"Failed to delete trainer: {str(e)}")

class TrainerMemberListView(views.APIView):
    permission_classes = [IsTrainer]

    @swagger_auto_schema(tags=['Trainer'], operation_summary='List assigned members')
    def get(self, request):
        """Get members assigned to trainer or who have sessions with the trainer"""
        try:
            trainer = Trainer.objects.get(user=request.user)
            # Members assigned directly OR who have booked sessions with this trainer
            members = Member.objects.filter(
                Q(assigned_trainer=trainer) | Q(booked_sessions__trainer=trainer)
            ).select_related('user').distinct()
            serializer = MemberSerializer(members, many=True)
            return handle_success(data=serializer.data, message="Assigned members retrieved successfully")
        except Trainer.DoesNotExist:
            return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)

class MemberProfileUpdateView(views.APIView):
    permission_classes = [IsMember]

    @swagger_auto_schema(
        tags=['Members'],
        operation_summary='Get current member profile',
        responses={200: MemberSerializer()}
    )
    def get(self, request):
        """Get the logged-in member's profile"""
        try:
            member = Member.objects.get(user=request.user)
            serializer = MemberSerializer(member)
            return handle_success(data=serializer.data, message="Profile retrieved successfully", status_code=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return handle_not_found(message="Member profile not found")

    @swagger_auto_schema(
        tags=['Members'],
        operation_summary='Update current member profile',
        request_body=MemberSerializer
    )
    def patch(self, request):
        """Update the logged-in member's profile"""
        try:
            member = Member.objects.get(user=request.user)
            user = request.user
            
            # Update user fields
            user_fields = ['first_name', 'last_name', 'phone']
            for field in user_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
            user.save()
            
            # Update member-specific fields
            if 'notes' in request.data:
                member.notes = request.data['notes']
            if 'address' in request.data:
                member.address = request.data['address']
            if 'emergency_contact' in request.data:
                member.emergency_contact = request.data['emergency_contact']
            member.save()
            
            serializer = MemberSerializer(member)
            return handle_success(data=serializer.data, message="Profile updated successfully", status_code=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return handle_not_found(message="Member profile not found")
        except Exception as e:
            return handle_error(message=f"Failed to update profile: {str(e)}")

class MemberListView(views.APIView):
    permission_classes = [IsAdminOrTrainer]

    @swagger_auto_schema(tags=['Members'], operation_summary='List all members')
    def get(self, request):
        members = Member.objects.select_related('user', 'assigned_trainer__user').prefetch_related('subscriptions__plan').all()
        serializer = MemberSerializer(members, many=True)
        return handle_success(data=serializer.data, message="Members retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Members'], operation_summary='Create a new member', request_body=MemberSerializer)
    def post(self, request):
        serializer = MemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Member created successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class MemberDetailView(views.APIView):
    permission_classes = [IsAdminOrTrainer]

    def get_object(self, pk):
        try:
            return Member.objects.get(pk=pk)
        except Member.DoesNotExist:
            return None

    @swagger_auto_schema(tags=['Members'], operation_summary='Get member details')
    def get(self, request, pk):
        member = self.get_object(pk)
        if not member:
            return handle_not_found(message="Member not found")
        serializer = MemberSerializer(member)
        return handle_success(data=serializer.data, message="Member details retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Members'], operation_summary='Update member')
    def put(self, request, pk):
        member = self.get_object(pk)
        if not member:
            return handle_not_found(message="Member not found")
        
        old_trainer = member.assigned_trainer
        serializer = MemberSerializer(member, data=request.data, partial=True)
        if serializer.is_valid():
            member = serializer.save()
            
            # If trainer changed/assigned, notify the trainer
            new_trainer = member.assigned_trainer
            if new_trainer and new_trainer != old_trainer:
                Notification.objects.create(
                    recipient=new_trainer.user,
                    title="New Client Assigned",
                    message=f"You have been assigned a new client: {member.user.get_full_name()}."
                )

            return handle_success(data=serializer.data, message="Member updated successfully", status_code=status.HTTP_200_OK)
        return handle_validation_error(errors=serializer.errors)

    def patch(self, request, pk):
        return self.put(request, pk)

    @swagger_auto_schema(tags=['Members'], operation_summary='Delete member')
    def delete(self, request, pk):
        member = self.get_object(pk)
        if not member:
            return handle_not_found(message="Member not found")
        
        from django.db import transaction
        try:
            with transaction.atomic():
                user = member.user
                user.delete() # This will cascade delete member profile, attendance, etc.
            return handle_success(message="Member and associated user deleted successfully", status_code=status.HTTP_200_OK)
        except Exception as e:
            return handle_error(message=f"Failed to delete member: {str(e)}")

class GymSettingView(views.APIView):
    permission_classes = [IsAdminUser]

    def get_object(self):
        obj, created = GymSetting.objects.get_or_create(id=1)
        return obj

    @swagger_auto_schema(tags=['Settings'], operation_summary='Get gym settings')
    def get(self, request):
        settings = self.get_object()
        serializer = GymSettingSerializer(settings)
        return handle_success(data=serializer.data, message="Settings retrieved successfully")

    @swagger_auto_schema(tags=['Settings'], operation_summary='Update gym settings')
    def patch(self, request):
        settings = self.get_object()
        serializer = GymSettingSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Settings updated successfully")
        return handle_validation_error(errors=serializer.errors)
