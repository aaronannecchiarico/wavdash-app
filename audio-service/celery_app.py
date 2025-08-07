import sys
import os
from pathlib import Path

# Ensure project root is in Python path for worker processes
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from celery import Celery
from celery.signals import worker_ready, worker_shutting_down
import logging

from config import settings

celery_app = Celery(
    "audio_processing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "tasks.audio_processing",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
    task_routes={
        'tasks.audio_processing.process_audio_features': {'queue': 'audio_features'},
        'tasks.audio_processing.separate_audio_stems': {'queue': 'stem_separation'},
    },
    task_annotations={
        'tasks.audio_processing.process_audio_features': {'rate_limit': '10/m'},
        'tasks.audio_processing.separate_audio_stems': {'rate_limit': '5/m'},
    }
)

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    # Force CPU for MPS compatibility in worker processes
    import os
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    os.environ["PYTORCH_DISABLE_MPS_FALLBACK_WARNING"] = "1"
    
    # Disable MPS for Celery workers to prevent crashes
    import torch
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        logging.warning("MPS detected but using CPU for Celery worker to avoid multiprocessing issues")
    
    logging.info(f"Celery worker {sender.hostname} is ready")

@worker_shutting_down.connect
def worker_shutting_down_handler(sender=None, **kwargs):
    logging.info(f"Celery worker {sender.hostname} is shutting down")

if __name__ == '__main__':
    celery_app.start()