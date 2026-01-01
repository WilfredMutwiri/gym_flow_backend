from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    TrainerSerializer, MemberSerializer, AttendanceRecordSerializer, 
    ProgramSerializer, WorkoutDaySerializer, ExerciseSerializer, 
    WorkoutSetSerializer, SubscriptionPlanSerializer, 
    MemberSubscriptionSerializer, PaymentSerializer, 
    ProgressEntrySerializer, MessageSerializer, GymSettingSerializer
)
from .models import (
    Trainer, Member, AttendanceRecord, Program, WorkoutDay, Exercise, 
    WorkoutSet, SubscriptionPlan, MemberSubscription, Payment, 
    ProgressEntry, Message, GymSetting
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

    def patch(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        
        # Handle assigned_members separately if present
        assigned_members_ids = request.data.get('assigned_members')
        if assigned_members_ids is not None:
            # Remove assigned_members from data to avoid serializer issues
            data = {k: v for k, v in request.data.items() if k != 'assigned_members'}
            
            # Update other fields if any
            if data:
                serializer = ProgramSerializer(program, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return handle_validation_error(errors=serializer.errors)
            
            # Update assigned_members ManyToMany relationship
            program.assigned_members.set(assigned_members_ids)
            
            # Return updated program
            updated_serializer = ProgramSerializer(program)
            return handle_success(data=updated_serializer.data, message="Program updated successfully", status_code=status.HTTP_200_OK)
        else:
            # Normal update without assigned_members
            return self.put(request, pk)

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

class ReportsStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        tags=['Stats'],
        operation_summary='Get advanced reports statistics'
    )
    def get(self, request):
        try:
            today = timezone.now().date()
            
            # 1. Revenue Analysis (last 6 months)
            revenue_analysis = []
            for i in range(5, -1, -1):
                # Simple month calculation
                first_day = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                # Next month's first day
                next_month = (first_day + timedelta(days=32)).replace(day=1)
                
                amount = Payment.objects.filter(
                    status='completed',
                    transaction_date__range=[first_day, next_month - timedelta(days=1)]
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                revenue_analysis.append({
                    'month': first_day.strftime('%b %Y'),
                    'revenue': float(amount)
                })

            # 2. Attendance Trends (last 30 days)
            attendance_trends = []
            for i in range(29, -1, -1):
                d = today - timedelta(days=i)
                count = AttendanceRecord.objects.filter(date=d).count()
                attendance_trends.append({
                    'date': d.strftime('%Y-%m-%d'),
                    'count': count
                })

            # 3. Membership Distribution (by Plan)
            membership_distribution = []
            plans = SubscriptionPlan.objects.all()
            for plan in plans:
                count = Member.objects.filter(
                    subscriptions__plan=plan,
                    subscriptions__status='active'
                ).distinct().count()
                membership_distribution.append({
                    'name': plan.name,
                    'value': count
                })
            
            # Handle members without plans
            no_plan_count = Member.objects.exclude(
                subscriptions__status='active'
            ).count()
            if no_plan_count > 0:
                membership_distribution.append({
                    'name': 'No Plan',
                    'value': no_plan_count
                })

            # 4. Trainer Performance
            trainer_performance = []
            trainers = Trainer.objects.all()
            for trainer in trainers:
                member_count = Member.objects.filter(assigned_trainer=trainer).count()
                program_count = Program.objects.filter(created_by=trainer).count()
                
                trainer_performance.append({
                    'name': f"{trainer.user.first_name} {trainer.user.last_name}",
                    'members': member_count,
                    'programs': program_count,
                    'rating': 4.5 + (trainer.id % 5) * 0.1
                })

            data = {
                'revenue_analysis': revenue_analysis,
                'attendance_trends': attendance_trends,
                'membership_distribution': membership_distribution,
                'trainer_performance': trainer_performance
            }

            return handle_success(data=data, message="Reports stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")

class MemberDashboardStatsView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Stats'],
        operation_summary='Get member dashboard statistics'
    )
    def get(self, request):
        """Get dashboard stats for the logged-in member"""
        try:
            user = request.user
            
            # Ensure user is a member
            if user.role != 'member':
                return handle_error(message="This endpoint is for members only", status_code=status.HTTP_403_FORBIDDEN)
            
            try:
                member = Member.objects.get(user=user)
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
            
            today = timezone.now().date()
            
            # 1. Get active subscription
            active_subscription = member.subscriptions.filter(status='active').first()
            subscription_data = None
            days_until_expiry = 0
            
            if active_subscription:
                days_until_expiry = (active_subscription.end_date - today).days
                subscription_data = {
                    'id': active_subscription.id,
                    'plan_name': active_subscription.plan.name if active_subscription.plan else 'N/A',
                    'start_date': active_subscription.start_date,
                    'end_date': active_subscription.end_date,
                    'status': active_subscription.status,
                    'amount': float(active_subscription.amount),
                    'days_until_expiry': days_until_expiry
                }
            
            # 2. Get enrolled programs
            enrolled_programs = member.assigned_programs.filter(status='active')
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Member {member.id} ({member.user.email}) - Total programs: {member.assigned_programs.count()}, Active: {enrolled_programs.count()}")
            
            programs_data = []
            for program in enrolled_programs:
                programs_data.append({
                    'id': program.id,
                    'name': program.name,
                    'description': program.description,
                    'duration': program.duration,
                    'difficulty': program.difficulty,
                    'goal': program.goal,
                    'status': program.status
                })
            
            # 3. Calculate attendance streak
            attendance_records = AttendanceRecord.objects.filter(
                member=member
            ).order_by('-date')
            
            attendance_streak = 0
            if attendance_records.exists():
                current_date = today
                for record in attendance_records:
                    if record.date == current_date or record.date == current_date - timedelta(days=1):
                        attendance_streak += 1
                        current_date = record.date - timedelta(days=1)
                    else:
                        break
            
            # 4. Get recent progress entries
            progress_entries = ProgressEntry.objects.filter(
                member=member
            ).order_by('-date')[:2]
            
            weight_change = 0
            if progress_entries.count() >= 2:
                latest_weight = progress_entries[0].weight or 0
                previous_weight = progress_entries[1].weight or 0
                weight_change = latest_weight - previous_weight
            
            # 5. Attendance count (last 30 days)
            thirty_days_ago = today - timedelta(days=30)
            attendance_count = AttendanceRecord.objects.filter(
                member=member,
                date__gte=thirty_days_ago
            ).count()
            
            data = {
                'member_info': {
                    'id': member.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'email': user.email,
                    'status': member.status
                },
                'subscription': subscription_data,
                'programs': programs_data,
                'stats': {
                    'attendance_streak': attendance_streak,
                    'weight_change': float(weight_change),
                    'active_programs_count': enrolled_programs.count(),
                    'days_until_expiry': days_until_expiry,
                    'attendance_last_30_days': attendance_count
                }
            }
            
            return handle_success(data=data, message="Member dashboard stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")

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
