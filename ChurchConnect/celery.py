"""
Celery Configuration for ChurchConnect
Handles background tasks and periodic jobs
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'churchconnect.settings')

app = Celery('churchconnect')

# Load config from Django settings (namespace='CELERY')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule (Periodic Tasks)
app.conf.beat_schedule = {
    # Send event reminders every hour
    'send-event-reminders': {
        'task': 'apps.events.tasks.send_event_reminders',
        'schedule': crontab(minute=0),  # Every hour
    },
    
    # Clean old notifications daily
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    
    # Generate daily reports
    'generate-daily-reports': {
        'task': 'common.tasks.generate_daily_reports',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
    
    # Send birthday wishes
    'send-birthday-wishes': {
        'task': 'apps.members.tasks.send_birthday_wishes',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    
    # Sync payment status
    'sync-payment-status': {
        'task': 'apps.donations.tasks.sync_payment_status',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}

# Celery Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Lagos',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')