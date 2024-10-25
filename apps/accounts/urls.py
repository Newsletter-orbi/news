from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from .views import *

app_name = 'accounts'
 
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
#     path('activate/<uidb64>/<token>/', views.ActivateAccountView.as_view(), name='activate'),
 
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_done/', TemplateView.as_view(template_name="accounts/password_reset_done.html"), name='password_reset_done'),
    path('reset/done/', TemplateView.as_view(template_name="accounts/password_reset_complete.html"), name='password_reset_complete')    ,
 
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url=reverse_lazy('accounts:password_change_done')),
            name='password_change'),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'), name='password_change_done'),
#     path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    
    path('dashboard_redirect/', CustomDashboardRedirectView.as_view(), name='dashboard_redirect'),
    path('verify/', views.verify_user, name='verify_user'),
]
