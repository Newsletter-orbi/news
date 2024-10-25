from django.db import models
from django.conf import settings
from datetime import timedelta

class SubscriptionPlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=255)
    stripe_plan_id = models.CharField(max_length=255)
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    credit = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.name} - {self.get_plan_type_display()}"

class UserSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=255)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True) 
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.plan.get_plan_type_display()})"
 
class Payment(models.Model):
    user_subscription = models.ForeignKey('UserSubscription', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_subscription_id = models.CharField(max_length=255)  # This should be present
    transaction_id = models.CharField(max_length=255, null=True, blank=True)  # For Stripe transaction ID
    payment_method = models.CharField(max_length=100, null=True, blank=True)  # Method of payment
    currency = models.CharField(max_length=10, default='USD')  # Default currency
    billing_address = models.TextField(null=True, blank=True)  # Billing address for invoicing
    payment_status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='pending')  # Status of the payment
    paid = models.BooleanField(default=False)  # Paid or unpaid
    paid_at = models.DateTimeField(null=True, blank=True)  # Timestamp when payment was made
    failure_reason = models.TextField(null=True, blank=True)  # Reason for failed payment
    created_at = models.DateTimeField(auto_now_add=True)  # When the payment record was created

    def __str__(self):
        return f"Payment {self.stripe_subscription_id} - {self.get_payment_status_display()}"
