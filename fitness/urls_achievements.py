from django.urls import path
from .views import MemberAchievementView

urlpatterns = [
    path('member/', MemberAchievementView.as_view(), name='member-achievement-list'),
    path('member/<int:member_id>/', MemberAchievementView.as_view(), name='member-achievement-detail'),
]
