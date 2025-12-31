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
    ProgressEntrySerializer, MessageSerializer
)

class TrainerViewSet(viewsets.ModelViewSet):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

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

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class ProgressEntryViewSet(viewsets.ModelViewSet):
    queryset = ProgressEntry.objects.all()
    serializer_class = ProgressEntrySerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
