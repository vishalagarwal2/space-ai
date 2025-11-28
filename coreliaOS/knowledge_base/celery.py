import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coreliaOS.settings')

app = Celery('knowledge_base')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_max_retries=3,
    task_default_retry_delay=60,
)

app.conf.task_routes = {
    'knowledge_base.tasks.process_document': {'queue': 'document_processing'},
    'knowledge_base.tasks.generate_embeddings': {'queue': 'embeddings'},
    'knowledge_base.tasks.sync_data_source': {'queue': 'data_sync'},
    'knowledge_base.tasks.cleanup_expired_documents': {'queue': 'cleanup'},
}

app.conf.beat_schedule = {
    'cleanup-expired-documents': {
        'task': 'knowledge_base.tasks.cleanup_expired_documents',
        'schedule': 3600.0,
    },
    'sync-auto-sync-sources': {
        'task': 'knowledge_base.tasks.sync_auto_sync_sources',
        'schedule': 1800.0,
    },
    'update-usage-statistics': {
        'task': 'knowledge_base.tasks.update_usage_statistics',
        'schedule': 300.0,
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')