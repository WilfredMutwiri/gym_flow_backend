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
            month_start = today.replace(day=1)
            
            # Overview
            total_members = Member.objects.count()
            active_members = Member.objects.filter(status='active').count()
            today_attendance = AttendanceRecord.objects.filter(date=today).count()
            active_programs = Program.objects.filter(status='active').count()
            
            monthly_revenue = Payment.objects.filter(
                transaction_date__date__gte=month_start,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Alerts
            expiring_cutoff = today + timedelta(days=7)
            expiring_sub_count = MemberSubscription.objects.filter(
                end_date__gte=today,
                end_date__lte=expiring_cutoff,
                status='active'
            ).count()
            
            # Dropout alerts (no attendance in 7 days)
            seven_days_ago = today - timedelta(days=7)
            active_member_ids = Member.objects.filter(status='active').values_list('id', flat=True)
            recent_attendance_member_ids = AttendanceRecord.objects.filter(
                date__gte=seven_days_ago
            ).values_list('member_id', flat=True).distinct()
            dropout_alerts = len(set(active_member_ids) - set(recent_attendance_member_ids))
            
            new_members_this_month = Member.objects.filter(user__date_joined__date__gte=month_start).count()

            # Trends
            # Attendance trend (last 7 days for dashboard)
            seven_days_ago_trend = today - timedelta(days=7)
            attendance_query = AttendanceRecord.objects.filter(
                date__gte=seven_days_ago_trend
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            attendance_trend = [
                {
                    'date': item['date'].strftime('%a'),
                    'count': item['count']
                } for item in attendance_query
            ]

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

            # Expiring Subscriptions List
            expiring_subs = MemberSubscription.objects.filter(
                end_date__gte=today,
                end_date__lte=expiring_cutoff,
                status='active'
            ).select_related('member__user', 'plan')[:5]
            
            expiring_list = [
                {
                    'id': sub.id,
                    'memberName': f"{sub.member.user.first_name} {sub.member.user.last_name}",
                    'planName': sub.plan.name,
                    'endDate': sub.end_date.isoformat(),
                    'amount': float(sub.plan.price)
                } for sub in expiring_subs
            ]

            data = {
                'overview': {
                    'totalMembers': total_members,
                    'activeMembers': active_members,
                    'todayAttendance': today_attendance,
                    'monthlyRevenue': float(monthly_revenue),
                    'activePrograms': active_programs
                },
                'alerts': {
                    'expiringSubscriptions': expiring_sub_count,
                    'dropoutAlerts': dropout_alerts,
                    'newMembersThisMonth': new_members_this_month
                },
                'trends': {
                    'attendance': attendance_trend,
                    'revenue': revenue_trend
                },
                'expiringSubscriptionsList': expiring_list
            }
            return handle_success(data=data, message="Dashboard stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")

class ReportsStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Stats'], operation_summary='Get detailed reports and analytics')
    def get(self, request):
        try:
            today = timezone.now().date()
            
            # 1. Revenue Analysis (last 6 months)
            six_months_ago = today - timedelta(days=180)
            revenue_query = Payment.objects.filter(
                transaction_date__date__gte=six_months_ago.replace(day=1),
                status='completed'
            ).annotate(
                month_trunc=TruncMonth('transaction_date')
            ).values('month_trunc').annotate(
                total=Sum('amount')
            ).order_by('month_trunc')

            revenue_analysis = [
                {
                    'month': item['month_trunc'].strftime('%b'),
                    'revenue': float(item['total'])
                } for item in revenue_query
            ]

            # 2. Attendance trends (last 30 days)
            thirty_days_ago = today - timedelta(days=30)
            attendance_query = AttendanceRecord.objects.filter(
                date__gte=thirty_days_ago
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            attendance_trends = [
                {
                    'date': item['date'].strftime('%Y-%m-%d'),
                    'count': item['count']
                } for item in attendance_query
            ]

            # 3. Membership Distribution
            plans_data = SubscriptionPlan.objects.annotate(
                member_count=Count('membersubscription')
            ).values('name', 'member_count')

            membership_distribution = [
                {
                    'name': plan['name'],
                    'value': plan['member_count']
                } for plan in plans_data
            ]

            # 4. Trainer Performance
            trainers = Trainer.objects.select_related('user').annotate(
                members_count=Count('member', distinct=True),
                programs_count=Count('program', distinct=True)
            )

            trainer_performance = [
                {
                    'name': f"{t.user.first_name} {t.user.last_name}",
                    'members': t.members_count,
                    'programs': t.programs_count,
                    'rating': 4.5 # Placeholder until rating system added
                } for t in trainers
            ]

            data = {
                'revenue_analysis': revenue_analysis,
                'attendance_trends': attendance_trends,
                'membership_distribution': membership_distribution,
                'trainer_performance': trainer_performance
            }
            return handle_success(data=data, message="Reports stats retrieved successfully")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve reports: {str(e)}")

class MemberDashboardStatsView(views.APIView):
    permission_classes = [IsMember]

    @swagger_auto_schema(tags=['Stats'], operation_summary='Get member dashboard summary')
    def get(self, request):
        try:
            member = Member.objects.select_related('user').get(user=request.user)
            today = timezone.now().date()
            
            # 1. Member Info
            member_info = {
                'name': f"{member.user.first_name} {member.user.last_name}",
                'avatar': None # Placeholder
            }
            
            # 2. Subscription Info
            sub = MemberSubscription.objects.filter(member=member, status='active').select_related('plan').first()
            subscription = None
            days_until_expiry = 0
            if sub:
                days_until_expiry = (sub.end_date - today).days
                subscription = {
                    'plan_name': sub.plan.name,
                    'end_date': sub.end_date.isoformat(),
                    'status': sub.status,
                    'days_until_expiry': max(0, days_until_expiry)
                }
            
            # 3. Programs
            active_programs = list(member.assigned_programs.filter(status='active').values(
                'id', 'name', 'description', 'duration', 'difficulty', 'goal'
            ))

            # 4. Stats
            # Attendance streak
            streak = 0
            check_date = today
            # If no attendance today, check from yesterday
            if not AttendanceRecord.objects.filter(member=member, date=check_date).exists():
                check_date -= timedelta(days=1)
                
            while AttendanceRecord.objects.filter(member=member, date=check_date).exists():
                streak += 1
                check_date -= timedelta(days=1)
                if streak > 365: break # Safety break
            
            # Weight change (last 30 days or last two entries)
            weight_entries = ProgressEntry.objects.filter(member=member).order_by('-date')[:2]
            weight_change = 0
            if len(weight_entries) >= 2:
                weight_change = float(weight_entries[0].weight - weight_entries[1].weight)
            
            attendance_last_30 = AttendanceRecord.objects.filter(
                member=member, 
                date__gte=today - timedelta(days=30)
            ).count()

            data = {
                'member_info': member_info,
                'subscription': subscription,
                'programs': active_programs,
                'stats': {
                    'attendance_streak': streak,
                    'weight_change': weight_change,
                    'active_programs_count': len(active_programs),
                    'days_until_expiry': max(0, days_until_expiry),
                    'attendance_last_30_days': attendance_last_30
                }
            }
            return handle_success(data=data, message="Member dashboard stats retrieved successfully")
        except Member.DoesNotExist:
             return handle_error(message="Member profile not found")
        except Exception as e:
            return handle_error(message=f"Failed to retrieve stats: {str(e)}")
