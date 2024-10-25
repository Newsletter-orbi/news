from django.urls import path
from . import views
from .views import generate_invoice_pdf
 

urlpatterns = [
    path('', views.SubscriptionListView, name='subscription_list'),  # List all subscription plans
    path('checkout/<str:plan_id>/', views.CreateCheckoutSession, name='create_checkout_session'),
    path('success/', views.PaymentSuccessView, name='payment_success'),  # Payment success page
    path('failed/', views.PaymentFailedView, name='payment_failed'),  # Payment failed page
    path('generate-invoice/<str:session_id>/', generate_invoice_pdf, name='generate_invoice_pdf'),
]
