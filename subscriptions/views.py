from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import SubscriptionPlan, MemberSubscription, Payment
from .serializers import SubscriptionPlanSerializer, MemberSubscriptionSerializer, PaymentSerializer
from shared.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated, AllowAny
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)

class SubscriptionPlanListView(views.APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['Subscriptions'], operation_summary='List subscription plans')
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(status='active')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return handle_success(data=serializer.data, message="Subscription plans retrieved successfully", status_code=status.HTTP_200_OK)

class MemberSubscriptionListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Subscriptions'], operation_summary='List member subscriptions')
    def get(self, request):
        member_id = request.query_params.get('member')
        if member_id:
            subs = MemberSubscription.objects.filter(member_id=member_id)
        else:
            subs = MemberSubscription.objects.all()
        serializer = MemberSubscriptionSerializer(subs, many=True)
        return handle_success(data=serializer.data, message="Member subscriptions retrieved successfully", status_code=status.HTTP_200_OK)

class PaymentListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Payments'], operation_summary='List payments')
    def get(self, request):
        member_id = request.query_params.get('member')
        if member_id:
            payments = Payment.objects.filter(subscription__member_id=member_id)
        else:
            payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)
        return handle_success(data=serializer.data, message="Payments retrieved successfully", status_code=status.HTTP_200_OK)
