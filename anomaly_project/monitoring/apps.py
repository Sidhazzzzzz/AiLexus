import sys
import threading
from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'

    def ready(self):
        # Prevent running this when executing manage.py commands like migrate or makemigrations
        if not any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'collectstatic']):
            from . import website_checker
            # Start the website monitoring loop in a background thread
            t = threading.Thread(target=website_checker.run, daemon=True)
            t.start()
