from django.urls import path
from .views import (
    TrainerListView, TrainerDetailView, 
    MemberListView, MemberDetailView, 
    GymSettingView, TrainerMemberListView, MemberProfileUpdateView
)

urlpatterns = [
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
    path('members/', MemberListView.as_view(), name='member-list'),
    path('members/<int:pk>/', MemberDetailView.as_view(), name='member-detail'),
    path('settings/', GymSettingView.as_view(), name='gym-settings'),
    path('trainer/members/', TrainerMemberListView.as_view(), name='trainer-member-list'),
    path('profile/', MemberProfileUpdateView.as_view(), name='member-profile'),
]
