from django.urls import path
from .views import *
 
app_name = 'Newsletter'
 
urlpatterns = [
    path('create/', NewsletterCreateView.as_view(), name='newsletter_create'),
    path('<int:pk>/', NewsletterDetailView.as_view(), name='newsletter_detail'),
    path('edit/<int:pk>/', NewsletterEditView.as_view(), name='newsletter_edit'),
    path('delete/<int:pk>/', NewsletterDeleteView.as_view(), name='newsletter_delete'),
]