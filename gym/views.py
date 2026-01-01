from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
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
from .permissions import IsAdminUser, IsTrainer, IsMember, IsAdminOrTrainer
from rest_framework.permissions import AllowAny, IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)

class TrainerListView(views.APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        tags=['Trainers'],
        operation_summary='List all trainers',
        responses={200: TrainerSerializer(many=True)}
    )
    def get(self, request):
        trainers = Trainer.objects.all()
        serializer = TrainerSerializer(trainers, many=True)
        return handle_success(data=serializer.data, message="Trainers retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['Trainers'],
        operation_summary='Create a new trainer',
        request_body=TrainerSerializer,
        responses={201: TrainerSerializer()}
    )
    def post(self, request):
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

class MemberListView(views.APIView):
    permission_classes = [IsAdminOrTrainer]

    @swagger_auto_schema(tags=['Members'], operation_summary='List all members')
    def get(self, request):
        members = Member.objects.all()
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
        serializer = MemberSerializer(member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Member updated successfully", status_code=status.HTTP_200_OK)
        return handle_validation_error(errors=serializer.errors)

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

class ProgramListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Programs'], operation_summary='List all programs')
    def get(self, request):
        member_id = request.query_params.get('member')
        if member_id:
            programs = Program.objects.filter(assigned_members__id=member_id)
        else:
            programs = Program.objects.all()
        serializer = ProgramSerializer(programs, many=True)
        return handle_success(data=serializer.data, message="Programs retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Programs'], operation_summary='Create a new program', request_body=ProgramSerializer)
    def post(self, request):
        serializer = ProgramSerializer(data=request.data)
        if serializer.is_valid():
            if hasattr(request.user, 'trainer_profile'):
                serializer.save(created_by=request.user.trainer_profile)
            else:
                serializer.save()
            return handle_success(data=serializer.data, message="Program created successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class ProgramDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Program.objects.get(pk=pk)
        except Program.DoesNotExist:
            return None

    @swagger_auto_schema(tags=['Programs'], operation_summary='Get program details')
    def get(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        serializer = ProgramSerializer(program)
        return handle_success(data=serializer.data, message="Program details retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Programs'], operation_summary='Update program')
    def put(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        serializer = ProgramSerializer(program, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Program updated successfully", status_code=status.HTTP_200_OK)
        return handle_validation_error(errors=serializer.errors)

    @swagger_auto_schema(tags=['Programs'], operation_summary='Delete program')
    def delete(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        program.delete()
        return handle_success(message="Program deleted successfully", status_code=status.HTTP_200_OK)

from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

class DashboardStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        tags=['Stats'],
        operation_summary='Get dashboard statistics'
    )
    def get(self, request):
        try:
            today = timezone.now().date()
            start_of_month = today.replace(day=1)
            
            # 1. Overview Stats
            total_members = Member.objects.count()
            active_members = Member.objects.filter(status='active').count()
            today_attendance = AttendanceRecord.objects.filter(date=today).count()
            
            monthly_revenue = Payment.objects.filter(
                status='completed',
                transaction_date__gte=start_of_month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            active_programs = Program.objects.filter(status='active').count()
            
            # 2. Alerts
            expiring_soon = MemberSubscription.objects.filter(
                status='active',
                end_date__range=[today, today + timedelta(days=7)]
            )
            
            dropout_alerts = Member.objects.filter(
                status='active'
            ).exclude(
                attendance__date__gte=today - timedelta(days=7)
            ).count()
            
            new_members_this_month = Member.objects.filter(
                join_date__gte=start_of_month
            ).count()

            # 3. Trends (Attendance - last 7 days)
            attendance_trends = []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                count = AttendanceRecord.objects.filter(date=d).count()
                attendance_trends.append({
                    'date': d.strftime('%a'),
                    'count': count
                })

            # 4. Trends (Revenue - last 6 months)
            revenue_trends = []
            for i in range(5, -1, -1):
                # Simple month calculation
                month_date = (start_of_month - timedelta(days=i*30)).replace(day=1)
                next_month = (month_date + timedelta(days=32)).replace(day=1)
                
                rev = Payment.objects.filter(
                    status='completed',
                    transaction_date__range=[month_date, next_month]
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                revenue_trends.append({
                    'month': month_date.strftime('%b'),
                    'revenue': float(rev)
                })

            # 5. Serialization for Expiring Subscriptions
            expiring_data = []
            for sub in expiring_soon:
                expiring_data.append({
                    'id': sub.id,
                    'memberName': f"{sub.member.user.first_name} {sub.member.user.last_name}",
                    'planName': sub.plan.name if sub.plan else "N/A",
                    'endDate': sub.end_date,
                    'amount': float(sub.amount),
                    'status': sub.status
                })

            data = {
                'overview': {
                    'totalMembers': total_members,
                    'activeMembers': active_members,
                    'todayAttendance': today_attendance,
                    'monthlyRevenue': float(monthly_revenue),
                    'activePrograms': active_programs,
                },
                'alerts': {
                    'expiringSubscriptions': len(expiring_data),
                    'dropoutAlerts': dropout_alerts,
                    'newMembersThisMonth': new_members_this_month,
                },
                'trends': {
                    'attendance': attendance_trends,
                    'revenue': revenue_trends,
                },
                'expiringSubscriptionsList': expiring_data
            }

            return handle_success(data=data, message="Dashboard stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")

class AttendanceListView(views.APIView):
    permission_classes = [IsAdminOrTrainer]

    @swagger_auto_schema(tags=['Attendance'], operation_summary='List attendance records')
    def get(self, request):
        date = request.query_params.get('date')
        if date:
            records = AttendanceRecord.objects.filter(date=date)
        else:
            records = AttendanceRecord.objects.all()
        serializer = AttendanceRecordSerializer(records, many=True)
        return handle_success(data=serializer.data, message="Attendance records retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Attendance'], operation_summary='Create attendance record', request_body=AttendanceRecordSerializer)
    def post(self, request):
        serializer = AttendanceRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Attendance record created successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class WorkoutDayListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Workouts'], operation_summary='Create workout day', request_body=WorkoutDaySerializer)
    def post(self, request):
        serializer = WorkoutDaySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Workout day created successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class WorkoutSetListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Workouts'], operation_summary='Add exercise to workout day', request_body=WorkoutSetSerializer)
    def post(self, request):
        serializer = WorkoutSetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Exercise added to workout day", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class SubscriptionPlanListView(views.APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['Subscriptions'], operation_summary='List subscription plans')
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(status='active')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return handle_success(data=serializer.data, message="Subscription plans retrieved successfully", status_code=status.HTTP_200_OK)

class MemberSubscriptionListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Subscriptions'], operation_summary='List member subscriptions')
    def get(self, request):
        member_id = request.query_params.get('member')
        if member_id:
            subs = MemberSubscription.objects.filter(member_id=member_id)
        else:
            subs = MemberSubscription.objects.all()
        serializer = MemberSubscriptionSerializer(subs, many=True)
        return handle_success(data=serializer.data, message="Member subscriptions retrieved successfully", status_code=status.HTTP_200_OK)

class PaymentListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Payments'], operation_summary='List payments')
    def get(self, request):
        member_id = request.query_params.get('member')
        if member_id:
            payments = Payment.objects.filter(subscription__member_id=member_id)
        else:
            payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)
        return handle_success(data=serializer.data, message="Payments retrieved successfully", status_code=status.HTTP_200_OK)

class ProgressEntryListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Progress'], operation_summary='List progress entries')
    def get(self, request):
        member_id = request.query_params.get('member')
        if member_id:
            entries = ProgressEntry.objects.filter(member_id=member_id)
        else:
            entries = ProgressEntry.objects.all()
        serializer = ProgressEntrySerializer(entries, many=True)
        return handle_success(data=serializer.data, message="Progress entries retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Progress'], operation_summary='Record progress', request_body=ProgressEntrySerializer)
    def post(self, request):
        serializer = ProgressEntrySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(recorded_by=request.user)
            return handle_success(data=serializer.data, message="Progress entry recorded successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class ExerciseListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Workouts'], operation_summary='List all exercises')
    def get(self, request):
        exercises = Exercise.objects.all()
        serializer = ExerciseSerializer(exercises, many=True)
        return handle_success(data=serializer.data, message="Exercises retrieved successfully", status_code=status.HTTP_200_OK)

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
