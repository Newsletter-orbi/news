from django.db.models.signals import post_save
from django.dispatch import receiver
from social_django.models import UserSocialAuth
from apps.newsletters.models import UserCredit

@receiver(post_save, sender=UserSocialAuth)
def give_welcome_credits(sender, instance, created, **kwargs):
    print("Signal reçu")  # Vérifiez si cela apparaît dans la console
    if created:
        user = instance.user
        if not UserCredit.objects.filter(user=user).exists():
            UserCredit.objects.create(user=user, credits=10)
            print(f"Crédits de bienvenue donnés à {user.email}")  # Debug
        else:
            print(f"L'utilisateur {user.email} a déjà des crédits")
    else:
        print(f"L'utilisateur {instance.user.email} existe déjà, aucun crédit ajouté")
