from __future__ import absolute_import, unicode_literals

import logging
import os

from celery import Celery, shared_task
from celery.signals import worker_shutting_down, worker_shutdown

logger = logging.getLogger(__name__)


@worker_shutting_down.connect
def handle_worker_shutting_down(sig, how, exitcode, **kwargs):
    """Called when worker receives shutdown signal."""
    from agent.shutdown import set_shutdown
    logger.info(f"Celery worker shutting down (signal={sig}, how={how})")
    set_shutdown()


@worker_shutdown.connect
def handle_worker_shutdown(sender, **kwargs):
    """Called after worker has shut down."""
    logger.info("Celery worker shutdown complete")

# Set the default Django settings mode for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent.settings')

app = Celery('agent')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'agent-cloud-ping-job-every-50-seconds': {
        'task': 'agent.tasks.send_ping_to_drd_cloud',
        'schedule': 50.0,  # Run every 50 seconds
    },
    'connector-test-connection-job-every-10-seconds': {
        'task': 'connectors.tasks.fetch_connector_connections_tests',
        'schedule': 10.0,  # Run every 10 seconds
    },
    'playbook-task-fetch-job-every-1-seconds': {
        'task': 'playbooks_engine.tasks.fetch_playbook_execution_tasks',
        'schedule': 1.0,  # Run every 1 seconds
    }
}

app.autodiscover_tasks()


@shared_task
def debug_task():
    logger.info('Debug task executed')
