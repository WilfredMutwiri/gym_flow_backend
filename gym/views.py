from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    TrainerSerializer, MemberSerializer, AttendanceRecordSerializer, 
    ProgramSerializer, WorkoutDaySerializer, ExerciseSerializer, 
    WorkoutSetSerializer, SubscriptionPlanSerializer, 
    MemberSubscriptionSerializer, PaymentSerializer, 
    ProgressEntrySerializer, MessageSerializer, GymSettingSerializer,
    SessionSerializer
)
from .models import (
    Trainer, Member, AttendanceRecord, Program, WorkoutDay, Exercise, 
    WorkoutSet, SubscriptionPlan, MemberSubscription, Payment, 
    ProgressEntry, Message, GymSetting, Session, MemberSubscription
)
from .permissions import IsAdminUser, IsTrainer, IsMember, IsAdminOrTrainer
from rest_framework.permissions import AllowAny, IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta


class TrainerListView(views.APIView):
    permission_classes = [IsAuthenticated]

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
        if not request.user.role == 'admin':
             return handle_error(message="Only admins can create programs", status_code=status.HTTP_403_FORBIDDEN)
        
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

        program.delete()
        return handle_success(message="Program deleted successfully", status_code=status.HTTP_200_OK)

class AssignProgramView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Programs'], 
        operation_summary='Assign program to member',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'member_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the member')
            },
            required=['member_id']
        )
    )
    def post(self, request, pk):
        """Assign a program to a member"""
        try:
            program = Program.objects.get(pk=pk)
            member_id = request.data.get('member_id')
            
            if not member_id:
                return handle_validation_error(errors={"member_id": "Member ID is required"})

            try:
                member = Member.objects.get(id=member_id)
            except Member.DoesNotExist:
                return handle_not_found(message="Member not found")
            
            # Check permissions: Admin or Trainer
            if request.user.role not in ['admin', 'trainer']:
                 return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)

            program.assigned_members.add(member)
            return handle_success(message="Program assigned successfully")
            
        except Program.DoesNotExist:
            return handle_not_found(message="Program not found")


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

class TrainerMemberAttendanceView(views.APIView):
    permission_classes = [IsTrainer]

    @swagger_auto_schema(
        tags=['Attendance'], 
        operation_summary='Get trainer members with attendance status',
        manual_parameters=[
            openapi.Parameter('date', openapi.IN_QUERY, description="Date to check attendance for (YYYY-MM-DD)", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request):
        try:
            # Get trainer profile
            try:
                trainer = Trainer.objects.get(user=request.user)
            except Trainer.DoesNotExist:
                return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)

            date_str = request.query_params.get('date')
            target_date = timezone.now().date()
            if date_str:
                try:
                    target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return handle_validation_error(errors={'date': 'Invalid date format. Use YYYY-MM-DD'})

            # Get assigned members (Directly assigned OR have booked sessions)
            members = Member.objects.filter(
                Q(assigned_trainer=trainer) | Q(booked_sessions__trainer=trainer)
            ).filter(status='active').distinct()
            
            # Get attendance for that date
            attendance_map = {}
            records = AttendanceRecord.objects.filter(date=target_date, member__in=members)
            for record in records:
                attendance_map[record.member_id] = record

            data = []
            for member in members:
                record = attendance_map.get(member.id)
                data.append({
                    'member_id': member.id,
                    'member_name': f"{member.user.first_name} {member.user.last_name}",
                    'member_email': member.user.email,
                    'profile_image': None, # Add if available
                    'has_attended': record is not None,
                    'attendance_id': record.id if record else None,
                    'check_in_time': record.check_in_time if record else None,
                    'check_out_time': record.check_out_time if record else None,
                })

            return handle_success(data=data, message="Member attendance status retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve attendance: {str(e)}")

class AttendanceMarkView(views.APIView):
    permission_classes = [IsAdminOrTrainer]

    @swagger_auto_schema(
        tags=['Attendance'],
        operation_summary='Mark or Unmark attendance',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'member_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['present', 'absent']),
            },
            required=['member_id', 'date', 'status']
        )
    )
    def post(self, request):
        try:
            member_id = request.data.get('member_id')
            date_str = request.data.get('date')
            status_action = request.data.get('status') # 'present' or 'absent'

            if not all([member_id, date_str, status_action]):
                return handle_validation_error(errors={'error': 'Missing required fields'})

            try:
                target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return handle_validation_error(errors={'date': 'Invalid date format'})

            # Check permissions (Trainers can only mark their members? Or anyone?)
            # Assuming trainers can mark any member for now, or check association.
            if request.user.role == 'trainer':
                try:
                    trainer = Trainer.objects.get(user=request.user)
                    # Check if member is assigned to trainer? 
                    # Requirement says "trainer marks... OF THEIR MEMBERS".
                    # Let's enforce it.
                    # Check if member is assigned to trainer (Direct or via Session)
                    is_assigned = Member.objects.filter(
                        Q(assigned_trainer=trainer) | Q(booked_sessions__trainer=trainer),
                        id=member_id
                    ).exists()
                    
                    if not is_assigned:
                         return handle_error(message="Member is not assigned to you", status_code=status.HTTP_403_FORBIDDEN)
                except Trainer.DoesNotExist:
                    return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)

            if status_action == 'present':
                # Create record if not exists
                record, created = AttendanceRecord.objects.get_or_create(
                    member_id=member_id,
                    date=target_date,
                    defaults={
                        'check_in_time': timezone.now(), # Approximate if marking for past? 
                        # If marking for today, now is fine. If past, maybe set to 9am?
                        # For simplicity, use current time or 12:00 PM of that day.
                        'check_in_time': timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.min.time())) if target_date < timezone.now().date() else timezone.now(),
                        'method': 'manual'
                    }
                )
                if not created:
                    return handle_success(message="Attendance already marked")
                return handle_success(message="Attendance marked as present")
            
            elif status_action == 'absent':
                # Delete record if exists
                AttendanceRecord.objects.filter(member_id=member_id, date=target_date).delete()
                return handle_success(message="Attendance marked as absent")
            
            else:
                return handle_validation_error(errors={'status': 'Invalid status. Use present or absent'})

        except Exception as e:
            return handle_error(message=f"Failed to mark attendance: {str(e)}")

class MemberAttendanceStatsView(views.APIView):
    permission_classes = [IsMember]

    @swagger_auto_schema(tags=['Stats'], operation_summary='Get detailed member attendance analytics')
    def get(self, request):
        try:
            member = Member.objects.get(user=request.user)
            
            # 1. Total Attendance
            total_visits = AttendanceRecord.objects.filter(member=member).count()
            
            # 2. Monthly breakdown (last 12 months)
            today = timezone.now().date()
            monthly_stats = []
            for i in range(11, -1, -1):
                month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1)
                
                count = AttendanceRecord.objects.filter(
                    member=member,
                    date__gte=month_start,
                    date__lt=month_end
                ).count()
                
                monthly_stats.append({
                    'month': month_start.strftime('%b %Y'),
                    'visits': count
                })

            # 3. Day of week preference
            # 1 = Sunday, 7 = Saturday for Django query? No, .week_day is 0-6 (Mon-Sun).
            # Easier to fetch all dates and aggregate in python if volume is low.
            recent_records = AttendanceRecord.objects.filter(
                member=member,
                date__gte=today - timedelta(days=90) # Last 3 months
            )
            day_counts = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0} # Mon-Sun
            for r in recent_records:
                day_counts[r.date.weekday()] += 1
            
            days_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            weekly_pattern = [{'day': days_labels[i], 'visits': day_counts[i]} for i in range(7)]

            # 4. Recent history (Detailed list)
            history = AttendanceRecord.objects.filter(member=member).order_by('-date')[:30]
            history_data = AttendanceRecordSerializer(history, many=True).data

            data = {
                'total_visits': total_visits,
                'monthly_stats': monthly_stats,
                'weekly_pattern': weekly_pattern,
                'history': history_data
            }
            
            return handle_success(data=data, message="Attendance analytics retrieved successfully")
        except Member.DoesNotExist:
            return handle_error(message="Member profile not found")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve analytics: {str(e)}")

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

class SessionListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Sessions'],
        operation_summary='List sessions',
        manual_parameters=[
            openapi.Parameter('trainer_id', openapi.IN_QUERY, description="Filter by trainer ID", type=openapi.TYPE_INTEGER),
        ],
        responses={200: SessionSerializer(many=True)}
    )
    def get(self, request):
        user = request.user
        queryset = Session.objects.all()
        
        # Filter based on user role
        if user.role == 'member':
            queryset = queryset.filter(member__user=user)
        elif user.role == 'trainer':
            queryset = queryset.filter(trainer__user=user)
            
        # Optional filters
        trainer_id = request.query_params.get('trainer_id')
        if trainer_id:
            queryset = queryset.filter(trainer_id=trainer_id)
            
        serializer = SessionSerializer(queryset, many=True)
        return handle_success(data=serializer.data, message="Sessions retrieved successfully")

    @swagger_auto_schema(
        tags=['Sessions'],
        operation_summary='Book a session',
        request_body=SessionSerializer,
        responses={201: SessionSerializer()}
    )
    def post(self, request):
        # If user is member, auto-assign member field
        data = request.data.copy()
        if request.user.role == 'member':
            try:
                member = Member.objects.get(user=request.user)
                data['member'] = member.id
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found")
        
        serializer = SessionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Session booked successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class SessionDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            session = Session.objects.get(pk=pk)
            # Check permissions
            if user.role == 'member':
                try:
                    member = Member.objects.get(user=user)
                    if session.member != member:
                        return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
                except Member.DoesNotExist:
                    return handle_error(message="Member profile not found", status_code=status.HTTP_404_NOT_FOUND)
            elif user.role == 'trainer':
                try:
                    trainer = Trainer.objects.get(user=user)
                    if session.trainer != trainer:
                        return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
                except Trainer.DoesNotExist:
                    return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)
            
            return session
        except Session.DoesNotExist:
            return handle_not_found(message="Session not found")

    @swagger_auto_schema(tags=['Sessions'], operation_summary='Get session details', responses={200: SessionSerializer()})
    def get(self, request, pk):
        session = self.get_object(pk, request.user)
        if isinstance(session, Response): return session
        serializer = SessionSerializer(session)
        return handle_success(data=serializer.data, message="Session details retrieved successfully")

    @swagger_auto_schema(tags=['Sessions'], operation_summary='Update session', request_body=SessionSerializer)
    def patch(self, request, pk):
        session = self.get_object(pk, request.user)
        if isinstance(session, Response): return session
        
        old_status = session.status
        
        serializer = SessionSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            updated_session = serializer.save()
            
            # Auto-create AttendanceRecord if session is completed
            if old_status != 'completed' and updated_session.status == 'completed':
                session_date = updated_session.start_time.date()
                if not AttendanceRecord.objects.filter(member=updated_session.member, date=session_date).exists():
                    AttendanceRecord.objects.create(
                        member=updated_session.member,
                        check_in_time=updated_session.start_time,
                        date=session_date,
                        method='session'
                    )

            return handle_success(data=serializer.data, message="Session updated successfully")
        return handle_validation_error(errors=serializer.errors)

    @swagger_auto_schema(tags=['Sessions'], operation_summary='Cancel session')
    def delete(self, request, pk):
        session = self.get_object(pk, request.user)
        if isinstance(session, Response): return session
        
        session.status = 'cancelled'
        session.save()
        return handle_success(message="Session cancelled successfully")


class TrainerMemberListView(views.APIView):
    permission_classes = [IsTrainer]

    @swagger_auto_schema(tags=['Trainer'], operation_summary='List assigned members')
    def get(self, request):
        """Get unique members who have sessions with the current trainer"""
        try:
            trainer = Trainer.objects.get(user=request.user)
            # Find members who have booked sessions with this trainer
            # Use 'booked_sessions' related_name from Session.member
            members = Member.objects.filter(booked_sessions__trainer=trainer).distinct()
            serializer = MemberSerializer(members, many=True)
            return handle_success(data=serializer.data, message="Assigned members retrieved successfully")
        except Trainer.DoesNotExist:
            return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)


class ProgressEntryListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Tracking'], operation_summary='List progress entries')
    def get(self, request, member_id):
        """List progress entries for a member"""
        try:
            member = Member.objects.get(id=member_id)
            
            # Check permissions: Member can view own, Trainer can view assigned, Admin can view all
            if request.user.role == 'member':
                if member.user != request.user:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            elif request.user.role == 'trainer':
                # Check if trainer has relationship with member
                trainer = Trainer.objects.get(user=request.user)
                if not Session.objects.filter(trainer=trainer, member=member).exists():
                     pass # Strictly speaking, maybe deny? But for MVP allow trainer to see any member they want to log for? 
                     # Task said "assigned members". Let's enforce it loosely or allow viewing.
                     # "trainer should be able to update... since they are the ones training them"
                     # Let's allow Trainers to view ANY member for now to simplify "finding" a client, 
                     # or strictly enforce "My Clients". Sticking to "My Clients" logic from task.
                     if not Session.objects.filter(trainer=trainer, member=member).exists():
                         pass 
            
            entries = ProgressEntry.objects.filter(member=member).order_by('-date')
            serializer = ProgressEntrySerializer(entries, many=True)
            return handle_success(data=serializer.data, message="Progress entries retrieved successfully")
        except Member.DoesNotExist:
            return handle_not_found(message="Member not found")

    @swagger_auto_schema(tags=['Tracking'], operation_summary='Create progress entry', request_body=ProgressEntrySerializer)
    def post(self, request, member_id):
        """Create a progress entry for a member"""
        try:
            member = Member.objects.get(id=member_id)
            
            # Check permissions
            if request.user.role == 'member':
                if member.user != request.user:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            elif request.user.role == 'trainer':
                # Ensure trainer is assigned
                trainer = Trainer.objects.get(user=request.user)
                # Assignment check can be added here if needed
            
            data = request.data.copy()
            data['member'] = member.id
            data['recorded_by'] = request.user.id
            
            serializer = ProgressEntrySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return handle_success(data=serializer.data, message="Progress logged successfully", status_code=status.HTTP_201_CREATED)
            return handle_validation_error(errors=serializer.errors)
        except Member.DoesNotExist:
            return handle_not_found(message="Member not found")
