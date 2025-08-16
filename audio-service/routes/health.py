"""
Health and System Routes
Handles health checks, system status, and general API information
"""

from fastapi import APIRouter

from celery_app import celery_app
from services.storage_service import is_storage_enabled, get_storage_type

router = APIRouter(tags=["Health & System"])


@router.get("/")
async def root():
    """API root endpoint"""
    return {"message": "Audio Processing Microservice", "version": "1.0.0"}


@router.get("/health")
async def health_check():
    """Comprehensive health check for all system components"""
    from utils.device_utils import get_device_info, get_memory_usage
    
    device_info = get_device_info()
    memory_usage = get_memory_usage()
    redis_status = celery_app.control.ping()
    
    # Check storage configuration
    storage_enabled = is_storage_enabled()
    storage_type = get_storage_type().value if storage_enabled else "unavailable"
    
    return {
        "status": "healthy", 
        "redis_connected": redis_status,
        "device_info": device_info,
        "memory_usage": memory_usage,
        "storage_enabled": storage_enabled,
        "storage_type": storage_type
    }