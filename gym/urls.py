from django.urls import path
from .views import (
    TrainerListView, TrainerDetailView,
    MemberListView, MemberDetailView,
    ProgramListView, ProgramDetailView, AssignProgramView,
    AttendanceListView, WorkoutDayListView,
    WorkoutSetListView, SubscriptionPlanListView,
    MemberSubscriptionListView, PaymentListView,
    ProgressEntryListView, ExerciseListView,
    MessageListView, DashboardStatsView, ReportsStatsView, MemberDashboardStatsView, GymSettingView,
    MemberProfileUpdateView,
    SessionListView, SessionDetailView,
    TrainerMemberListView, TrainerMemberAttendanceView, AttendanceMarkView, MemberAttendanceStatsView,
    AchievementListView, MemberAchievementView, NotificationListView
)
from .chat_views import ConversationListView, ConversationDetailView, MemberListForChatView

urlpatterns = [
    # Settings
    path('settings/', GymSettingView.as_view(), name='gym-settings'),
    # Dashboard Stats
    path('stats/dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('stats/reports/', ReportsStatsView.as_view(), name='reports-stats'),
    path('stats/member-dashboard/', MemberDashboardStatsView.as_view(), name='member-dashboard-stats'),
    path('stats/member-attendance/', MemberAttendanceStatsView.as_view(), name='member-attendance-stats'),
    # Member Profile
    path('profile/', MemberProfileUpdateView.as_view(), name='member-profile'),
    # Chat
    path('chat/conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('chat/conversations/<int:conversation_id>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('chat/members/', MemberListForChatView.as_view(), name='chat-members'),
    # Trainers
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
    
    # Members
    path('members/', MemberListView.as_view(), name='member-list'),
    path('members/<int:pk>/', MemberDetailView.as_view(), name='member-detail'),
    
    # Programs
    path('programs/', ProgramListView.as_view(), name='program-list'),
    path('programs/<int:pk>/', ProgramDetailView.as_view(), name='program-detail'),
    path('programs/<int:pk>/assign/', AssignProgramView.as_view(), name='program-assign'),
    
    # Sessions
    path('sessions/', SessionListView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', SessionDetailView.as_view(), name='session-detail'),

    # Trainer Members
    path('trainer/members/', TrainerMemberListView.as_view(), name='trainer-member-list'),
    path('trainer/attendance/', TrainerMemberAttendanceView.as_view(), name='trainer-attendance-list'),
    # Member Progress
    path('members/<int:member_id>/progress/', ProgressEntryListView.as_view(), name='member-progress-list'),
    
    # Other Entities
    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/mark/', AttendanceMarkView.as_view(), name='attendance-mark'),
    path('workout-days/', WorkoutDayListView.as_view(), name='workout-day-list'),
    path('workout-sets/', WorkoutSetListView.as_view(), name='workout-set-list'),
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),
    path('subscriptions/', MemberSubscriptionListView.as_view(), name='subscription-list'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('progress/', ProgressEntryListView.as_view(), name='progress-list'),
    path('exercises/', ExerciseListView.as_view(), name='exercise-list'),
    path('messages/', MessageListView.as_view(), name='message-list'),
    
    # Achievements
    path('achievements/', AchievementListView.as_view(), name='achievement-list'),
    path('achievements/member/', MemberAchievementView.as_view(), name='member-achievement-list'),
    path('achievements/member/<int:member_id>/', MemberAchievementView.as_view(), name='member-achievement-detail'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', NotificationListView.as_view(), name='notification-read'),
]
