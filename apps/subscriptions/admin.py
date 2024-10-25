from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, Payment

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'stripe_plan_id')
    list_filter = ('plan_type',)
    search_fields = ('name', 'stripe_plan_id')
    ordering = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'active', 'start_date', 'end_date')
    list_filter = ('plan__name', 'active')
    search_fields = ('user__username', 'plan__name', 'stripe_subscription_id')
    ordering = ('user', 'start_date')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user_subscription', 'amount', 'paid', 'created_at')
    list_filter = ('paid', 'created_at')
    search_fields = ('user_subscription__user__username', 'stripe_payment_intent_id')
    ordering = ('-created_at',)
