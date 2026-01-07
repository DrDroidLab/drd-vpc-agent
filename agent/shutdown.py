"""
Graceful shutdown management for Celery workers.

Provides:
- Global shutdown state tracking
- Utility for tasks to check shutdown status
"""
import logging
import threading

logger = logging.getLogger(__name__)

# Thread-safe shutdown state
_shutdown_event = threading.Event()
_shutdown_lock = threading.Lock()


def is_shutting_down():
    """Check if worker is in shutdown mode. Call this in long-running tasks."""
    return _shutdown_event.is_set()


def set_shutdown():
    """Mark the worker as shutting down."""
    with _shutdown_lock:
        if not _shutdown_event.is_set():
            logger.info("Graceful shutdown initiated - completing in-flight tasks")
            _shutdown_event.set()
