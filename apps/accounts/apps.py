from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

def ready(self):
    print("App is ready, trying to import signals...")
    try:
        from . import signals
        print("Signals imported successfully!")
    except Exception as e:
        print(f"Error importing signals: {e}")
