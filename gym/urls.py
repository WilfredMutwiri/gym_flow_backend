from django.urls import path, include
from gym.views import DashboardStatsView, ReportsStatsView, MemberDashboardStatsView
from attendance.views import MemberAttendanceStatsView, TrainerMemberAttendanceView
from fitness.views import ProgressEntryListView
from subscriptions.views import SubscriptionPlanListView, MemberSubscriptionListView, PaymentListView
from chat.views import MessageListView

urlpatterns = [
    # Dashboard & Reports Stats (Keeping in gym app for now)
    path('stats/dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('stats/reports/', ReportsStatsView.as_view(), name='reports-stats'),
    path('stats/member-dashboard/', MemberDashboardStatsView.as_view(), name='member-dashboard-stats'),
    
    # Compatibility Mappings (Cross-app or legacy paths)
    path('stats/member-attendance/', MemberAttendanceStatsView.as_view(), name='member-attendance-stats'),
    path('trainer/attendance/', TrainerMemberAttendanceView.as_view(), name='trainer-attendance-list'),
    path('members/<int:member_id>/progress/', ProgressEntryListView.as_view(), name='member-progress-list'),
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),
    path('subscriptions/', MemberSubscriptionListView.as_view(), name='subscription-list'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('messages/', MessageListView.as_view(), name='message-list'),
    path('workout-days/', include('programs.urls_days')),
    path('workout-sets/', include('programs.urls_sets')),
    path('exercises/', include('programs.urls_exercises')),
    path('progress/', include('fitness.urls_progress')),
    path('achievements/', include('fitness.urls_achievements')),
    
    # Base App URLs
    path('', include('core.urls')),
    path('attendance/', include('attendance.urls')),
    path('programs/', include('programs.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
    path('fitness/', include('fitness.urls')),
    path('sessions/', include('scheduling.urls')), 
]
