from django.urls import path
from . import views
from .views import *

from .views import PaymentListView 
from apps.subscriptions.views import  generate_invoice_pdf
from .views import *
from .views import site_create_view

from .views import social_token_list_view, social_token_edit_view
from .views import social_app_list_view, social_app_edit_view
from .views import social_account_list_view, social_account_edit_view

app_name = 'custom_admin'


urlpatterns = [
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),

    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # Credit management
    path('credits/', views.CreditListView.as_view(), name='credit_list'),
    path('credits/<int:pk>/edit/', views.CreditUpdateView.as_view(), name='credit_edit'),
    path('credits/add/', AddCreditToUserView.as_view(), name='add_credit_to_user'),

    # News management
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/add/', views.NewsCreateView.as_view(), name='news_add'),
    path('news/<int:pk>/edit/', views.NewsUpdateView.as_view(), name='news_edit'),
    path('news/<int:pk>/delete/', views.NewsDeleteView.as_view(), name='news_delete'),
 
    # Newsletter management
    path('newsletter/', views.NewsletterListView.as_view(), name='newsletter_list'),
    path('newsletter/add/', views.NewsletterCreateView.as_view(), name='newsletter_add'),
    path('newsletter/<int:pk>/edit/', views.NewsletterUpdateView.as_view(), name='newsletter_edit'),
    path('newsletter/<int:pk>/delete/', views.NewsletterDeleteView.as_view(), name='newsletter_delete'),

    # Subscription management
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription_list'),
    path('subscriptions/add/', SubscriptionCreateView.as_view(), name='subscription_add'),
    path('subscriptions/<int:pk>/edit/', views.SubscriptionUpdateView.as_view(), name='subscription_edit'),

    path('paiements/', PaymentListView.as_view(), name='paiement_list'),
    path('paiements/invoice/<str:subscription_id>/',  generate_invoice_pdf, name='generate_invoice_pdf'),
 
    path('manage-groups/', manage_groups, name='manage_groups'),
    path('update-group/<int:group_id>/', update_group, name='update_group'),
    path('manage-permissions/', manage_permissions, name='manage_permissions'),
    
    path('sites/', site_list_view, name='site_list'),
    path('sites/create/', site_create_view, name='create_site'),  # URL pour créer un nouveau site
    path('sites/edit/<int:site_id>/', site_edit_view, name='edit_site'),
  
    path('social-accounts/', social_account_list_view, name='social_account_list'),
    path('social-accounts/create/', social_account_create_view, name='create_social_account'),
    path('social-accounts/edit/<int:account_id>/', social_account_edit_view, name='edit_social_account'),

    path('social-tokens/', social_token_list_view, name='social_token_list'),
    path('social-tokens/create/', social_token_create_view, name='create_social_token'),
    path('social-tokens/edit/<int:token_id>/', social_token_edit_view, name='edit_social_token'),

    path('social-apps/', social_app_list_view, name='social_app_list'),
    path('social-apps/create/', social_app_create_view, name='create_social_app'),
    path('social-apps/edit/<int:app_id>/', social_app_edit_view, name='edit_social_app'),
  

]

