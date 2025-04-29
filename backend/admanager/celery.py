import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admanager.settings')

app = Celery('admanager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-brand-budgets-every-hour': {
        'task': 'api.tasks.update_brand_spend',
        'schedule': 10.0,
    },
    'enforce-dayparting-every-15-mins': {
        'task': 'api.tasks.ad_scheduler',
        'schedule': 10.0,
    },
}