from rest_framework import viewsets
from .models import (
    Trainer, Member, AttendanceRecord, Program, WorkoutDay, Exercise, 
    WorkoutSet, SubscriptionPlan, MemberSubscription, Payment, 
    ProgressEntry, Message
)
from .serializers import (
    TrainerSerializer, MemberSerializer, AttendanceRecordSerializer, 
    ProgramSerializer, WorkoutDaySerializer, ExerciseSerializer, 
    WorkoutSetSerializer, SubscriptionPlanSerializer, 
    MemberSubscriptionSerializer, PaymentSerializer, 
    ProgressEntrySerializer, MessageSerializer,
    MemberSubscriptionSerializer, SubscriptionPlanSerializer,
    PaymentSerializer
)
from .permissions import IsAdminUser, IsTrainer, IsMember, IsAdminOrTrainer
from rest_framework.permissions import AllowAny, IsAuthenticated

class TrainerViewSet(viewsets.ModelViewSet):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [IsAdminUser]

    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()
        user.delete()

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAdminOrTrainer]

    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()
        user.delete()


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        return queryset

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        member_id = self.request.query_params.get('member')
        if member_id:
            queryset = queryset.filter(assigned_members__id=member_id)
        return queryset

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'trainer_profile'):
            serializer.save(created_by=self.request.user.trainer_profile)
        else:
            serializer.save()

class WorkoutDayViewSet(viewsets.ModelViewSet):
    queryset = WorkoutDay.objects.all()
    serializer_class = WorkoutDaySerializer

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

class WorkoutSetViewSet(viewsets.ModelViewSet):
    queryset = WorkoutSet.objects.all()
    serializer_class = WorkoutSetSerializer

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer

class MemberSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = MemberSubscription.objects.all()
    serializer_class = MemberSubscriptionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        member_id = self.request.query_params.get('member')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        return queryset

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        member_id = self.request.query_params.get('member')
        if member_id:
            queryset = queryset.filter(subscription__member_id=member_id)
        return queryset

class ProgressEntryViewSet(viewsets.ModelViewSet):
    queryset = ProgressEntry.objects.all()
    serializer_class = ProgressEntrySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        member_id = self.request.query_params.get('member')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        return queryset

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
