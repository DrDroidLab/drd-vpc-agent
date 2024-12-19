from __future__ import absolute_import, unicode_literals

import logging
import os

from celery import Celery, shared_task

logger = logging.getLogger(__name__)

# Set the default Django settings mode for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent.settings')

app = Celery('agent')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'agent-cloud-ping-job-every-60-seconds': {
        'task': 'agent.tasks.send_ping_to_drd_cloud',
        'schedule': 60.0,  # Run every 60 seconds
    },
    'playbook-task-fetch-job-every-10-seconds': {
        'task': 'playbooks_engine.tasks.fetch_playbook_execution_tasks',
        'schedule': 10.0,  # Run every 10 seconds
    },
}

app.autodiscover_tasks()


@shared_task
def debug_task():
    logger.info('Debug task executed')
