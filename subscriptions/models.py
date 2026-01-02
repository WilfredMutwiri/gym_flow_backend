from django.db import models
from shared.basemodel import BaseModel

class SubscriptionPlan(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField()  # in days
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return self.name

class MemberSubscription(BaseModel):
    member = models.ForeignKey('core.Member', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, db_index=True)  # active, expired, cancelled
    payment_status = models.CharField(max_length=20, db_index=True) # paid, pending, overdue
    amount = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(BaseModel):
    subscription = models.ForeignKey(MemberSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)  # cash, card, etc
    status = models.CharField(max_length=20, db_index=True)  # completed, pending, failed
    transaction_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
