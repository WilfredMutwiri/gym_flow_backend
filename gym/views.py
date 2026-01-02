from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.models import Trainer, Member, GymSetting
from attendance.models import AttendanceRecord
from programs.models import Program, WorkoutDay, Exercise, WorkoutSet
from subscriptions.models import SubscriptionPlan, MemberSubscription, Payment
from fitness.models import ProgressEntry, MemberAchievement
from chat.models import Message
from scheduling.models import Session
from notifications.models import Notification

from shared.permissions import IsAdminUser, IsTrainer, IsMember, IsAdminOrTrainer
from rest_framework.permissions import AllowAny, IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from datetime import timedelta

# Dashboard Stats Views
class DashboardStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Stats'], operation_summary='Get dashboard overview statistics')
    def get(self, request):
        try:
            today = timezone.now().date()
            
            total_members = Member.objects.count()
            active_members = Member.objects.filter(status='active').count()
            today_attendance = AttendanceRecord.objects.filter(date=today).count()
            
            # Monthly Revenue
            month_start = today.replace(day=1)
            monthly_revenue = Payment.objects.filter(
                transaction_date__date__gte=month_start,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Revenue Trend (last 6 months)
            six_months_ago = today - timedelta(days=180)
            revenue_query = Payment.objects.filter(
                transaction_date__date__gte=six_months_ago.replace(day=1),
                status='completed'
            ).annotate(
                month_trunc=TruncMonth('transaction_date')
            ).values('month_trunc').annotate(
                total=Sum('amount')
            ).order_by('month_trunc')

            revenue_trend = [
                {
                    'month': item['month_trunc'].strftime('%b'),
                    'revenue': float(item['total'])
                } for item in revenue_query
            ]

            data = {
                'total_members': total_members,
                'active_members': active_members,
                'today_attendance': today_attendance,
                'monthly_revenue': float(monthly_revenue),
                'revenue_trend': revenue_trend
            }
            return handle_success(data=data, message="Dashboard stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")

class ReportsStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Stats'], operation_summary='Get detailed reports and analytics')
    def get(self, request):
        try:
            # Plan distribution
            plans_data = SubscriptionPlan.objects.annotate(
                member_count=Count('membersubscription')
            ).values('name', 'member_count')

            # Attendance trend (last 30 days)
            thirty_days_ago = today - timedelta(days=30)
            attendance_query = AttendanceRecord.objects.filter(
                date__gte=thirty_days_ago
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            attendance_trend = [
                {
                    'date': item['date'].strftime('%Y-%m-%d'),
                    'count': item['count']
                } for item in attendance_query
            ]

            data = {
                'plan_distribution': list(plans_data),
                'attendance_trend': attendance_trend
            }
            return handle_success(data=data, message="Reports stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve reports: {str(e)}")

class MemberDashboardStatsView(views.APIView):
    permission_classes = [IsMember]

    @swagger_auto_schema(tags=['Stats'], operation_summary='Get member dashboard summary')
    def get(self, request):
        try:
            member = Member.objects.get(user=request.user)
            
            # 1. Attendance consistency (last 30 days)
            today = timezone.now().date()
            last_30_days = AttendanceRecord.objects.filter(
                member=member,
                date__gte=today - timedelta(days=30)
            ).count()

            # 2. Next Session
            next_session = Session.objects.filter(
                member=member,
                start_time__gte=timezone.now(),
                status='confirmed'
            ).order_by('start_time').first()

            # 3. Active Program
            active_program = member.assigned_programs.filter(status='active').first()

            # 4. Recent Progress (Weight)
            latest_weight = ProgressEntry.objects.filter(member=member).order_by('-date').first()
            
            data = {
                'attendance_consistency': last_30_days,
                'next_session': {
                    'time': next_session.start_time if next_session else None,
                    'trainer': next_session.trainer.user.get_full_name() if next_session else None
                },
                'active_program': active_program.name if active_program else "No Active Program",
                'current_weight': latest_weight.weight if latest_weight else None
            }
            return handle_success(data=data, message="Member dashboard stats retrieved successfully")
        except Member.DoesNotExist:
             return handle_error(message="Member profile not found")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")
