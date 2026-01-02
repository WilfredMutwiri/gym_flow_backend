from rest_framework import serializers
from .models import SubscriptionPlan, MemberSubscription, Payment
from core.serializers import MemberSerializer

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class MemberSubscriptionSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = MemberSubscription
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    subscription_details = MemberSubscriptionSerializer(source='subscription', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
