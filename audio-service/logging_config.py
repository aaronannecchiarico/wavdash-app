import logging
import logging.config
from pathlib import Path
import time

from config import settings

# Ensure log directory exists
log_dir = Path(settings.LOG_FILE).parent
log_dir.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": settings.LOG_FILE,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": str(log_dir / "error.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "celery_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": str(log_dir / "celery.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        # Root logger
        "": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        # FastAPI/Uvicorn
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["file"],
            "propagate": False,
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        # Celery
        "celery": {
            "level": "INFO",
            "handlers": ["console", "celery_file"],
            "propagate": False,
        },
        "celery.task": {
            "level": "INFO",
            "handlers": ["console", "celery_file"],
            "propagate": False,
        },
        "celery.worker": {
            "level": "INFO",
            "handlers": ["console", "celery_file"],
            "propagate": False,
        },
        # Application specific
        "audio_processing": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "feature_extraction": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        # Third party libraries
        "librosa": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False,
        },
        "torch": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False,
        },
        "demucs": {
            "level": "INFO",
            "handlers": ["file"],
            "propagate": False,
        },
    },
}


def setup_logging():
    """Setup logging configuration"""
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        logger = logging.getLogger("audio_processing")
        logger.info("Logging configuration loaded successfully")
    except (ImportError, ValueError) as e:
        # Fallback to basic logging if JSON logger is not available
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.FileHandler(settings.LOG_FILE), logging.StreamHandler()],
        )
        logger = logging.getLogger("audio_processing")
        logger.warning(f"Using fallback logging configuration due to: {e}")
        logger.info("Basic logging configuration loaded successfully")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


# Performance logging decorator
def log_performance(func):
    """Decorator to log function execution time"""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(f"performance.{func.__module__}.{func.__name__}")
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function executed successfully in {execution_time:.4f} seconds"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function failed after {execution_time:.4f} seconds: {str(e)}"
            )
            raise

    return wrapper


# Context manager for request logging
class RequestLogger:
    """Context manager for logging request processing"""

    def __init__(self, request_id: str, operation: str):
        self.request_id = request_id
        self.operation = operation
        self.logger = get_logger("request")
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Request {self.request_id}: Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time

        if exc_type is None:
            self.logger.info(
                f"Request {self.request_id}: {self.operation} completed in {execution_time:.4f} seconds"
            )
        else:
            self.logger.error(
                f"Request {self.request_id}: {self.operation} failed after {execution_time:.4f} seconds: {exc_val}"
            )


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()
