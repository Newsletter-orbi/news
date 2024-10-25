from django_cron import CronJobBase, Schedule
from datetime import datetime
class ResetSubscriptionCronJob(CronJobBase):
    RUN_EVERY_MINS = 3  # Exemple de tâche à exécuter toutes les 3 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'subscriptions.reset_subscription_cron_job'  # Assurez-vous que l'identifiant est unique

    def do(self):
        from .models import UserSubscription, UserCredit

        today = datetime.now()
        expired_subscriptions = UserSubscription.objects.filter(end_date__lte=today, active=True)

        for subscription in expired_subscriptions:
            user_credit, created = UserCredit.objects.get_or_create(user=subscription.user)
            user_credit.credits = 0
            user_credit.save()

            subscription.active = False
            subscription.save()

            print(f"Crédits réinitialisés pour l'utilisateur: {subscription.user.username}")

 