from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Si l'utilisateur existe déjà, ne fais rien
        if sociallogin.is_existing:
            return
        
        # Si l'utilisateur n'est pas encore enregistré, rediriger ou créer un compte
        user_email = sociallogin.account.extra_data.get('email')
        if request.user.is_authenticated:
            return redirect(reverse('accounts:dashboard'))  # Redirige vers le tableau de bord
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from apps.newsletters.models import UserCredit

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Ajout de crédits si l'utilisateur est nouveau
        if not UserCredit.objects.filter(user=user).exists():
            UserCredit.objects.create(user=user, credits=10)
        return user