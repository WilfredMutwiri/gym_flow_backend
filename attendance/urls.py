from django.urls import path
from .views import (
    AttendanceListView, TrainerMemberAttendanceView, 
    AttendanceMarkView, MemberAttendanceStatsView
)

urlpatterns = [
    path('', AttendanceListView.as_view(), name='attendance-list'),
    path('trainer/', TrainerMemberAttendanceView.as_view(), name='trainer-attendance'),
    path('mark/', AttendanceMarkView.as_view(), name='attendance-mark'),
    path('stats/', MemberAttendanceStatsView.as_view(), name='member-attendance-stats'),
]
