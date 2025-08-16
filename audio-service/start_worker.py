#!/usr/bin/env python3

import subprocess
import sys
import logging
import os
from pathlib import Path

# Ensure project root is in Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logging_config import setup_logging

def main():
    """Start Celery worker with proper configuration"""
    setup_logging()
    logger = logging.getLogger("worker_startup")
    
    try:
        # Celery worker command
        cmd = [
            "celery",
            "-A", "celery_app",
            "worker",
            "--loglevel=info",
            "--concurrency=2",
            "--queues=audio_features,stem_separation,tempo_processing",
            "--max-tasks-per-child=100",
            "--prefetch-multiplier=1"
        ]
        
        logger.info("Starting Celery worker with command: %s", " ".join(cmd))
        
        # Start worker
        process = subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error("Failed to start Celery worker: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error starting worker: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()