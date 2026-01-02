from django.urls import path
from .views import (
    SubscriptionPlanListView, MemberSubscriptionListView, PaymentListView
)

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),
    path('member/', MemberSubscriptionListView.as_view(), name='member-subscription-list'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
]
