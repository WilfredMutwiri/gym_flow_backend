from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer
from core.models import Member, Trainer
from shared.permissions import IsAdminOrTrainer, IsTrainer, IsMember
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)
from django.utils import timezone
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from datetime import timedelta

class AttendanceListView(views.APIView):
    permission_classes = [IsAdminOrTrainer]

    @swagger_auto_schema(tags=['Attendance'], operation_summary='List attendance records')
    def get(self, request):
        date = request.query_params.get('date')
        if date:
            records = AttendanceRecord.objects.filter(date=date).select_related('member__user')
        else:
            records = AttendanceRecord.objects.select_related('member__user').all()
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

            members = Member.objects.filter(
                Q(assigned_trainer=trainer) | Q(booked_sessions__trainer=trainer)
            ).filter(status='active').select_related('user').distinct()
            
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
                    'profile_image': None,
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

            if request.user.role == 'trainer':
                try:
                    trainer = Trainer.objects.get(user=request.user)
                    is_assigned = Member.objects.filter(
                        Q(assigned_trainer=trainer) | Q(booked_sessions__trainer=trainer),
                        id=member_id
                    ).exists()
                    
                    if not is_assigned:
                         return handle_error(message="Member is not assigned to you", status_code=status.HTTP_403_FORBIDDEN)
                except Trainer.DoesNotExist:
                    return handle_error(message="Trainer profile not found", status_code=status.HTTP_404_NOT_FOUND)

            if status_action == 'present':
                record, created = AttendanceRecord.objects.get_or_create(
                    member_id=member_id,
                    date=target_date,
                    defaults={
                        'check_in_time': timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.min.time())) if target_date < timezone.now().date() else timezone.now(),
                        'method': 'manual'
                    }
                )
                if not created:
                    return handle_success(message="Attendance already marked")
                return handle_success(message="Attendance marked as present")
            
            elif status_action == 'absent':
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
            total_visits = AttendanceRecord.objects.filter(member=member).count()
            
            today = timezone.now().date()
            one_year_ago = today - timedelta(days=365)
            attendance_query = AttendanceRecord.objects.filter(
                member=member,
                date__gte=one_year_ago.replace(day=1)
            ).annotate(
                month_trunc=TruncMonth('date')
            ).values('month_trunc').annotate(
                count=Count('id')
            ).order_by('month_trunc')

            monthly_stats = [
                {
                    'month': item['month_trunc'].strftime('%b %Y'),
                    'count': item['count']
                } for item in attendance_query
            ]
                
            data = {
                'total_visits': total_visits,
                'monthly_stats': monthly_stats
            }
            return handle_success(data=data, message="Attendance stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")
