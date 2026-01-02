from django.urls import path
from .views import ProgressEntryListView, MemberAchievementView

urlpatterns = [
    path('progress/', ProgressEntryListView.as_view(), name='progress-list'),
    path('achievements/member/', MemberAchievementView.as_view(), name='member-achievement-list'),
    path('achievements/member/<int:member_id>/', MemberAchievementView.as_view(), name='member-achievement-detail'),
]
