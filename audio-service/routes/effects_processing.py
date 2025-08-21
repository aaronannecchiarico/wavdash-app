"""
Effects Processing Routes
Handles advanced audio effects processing with customizable effect chains
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import uuid

from models.effects_models import (
    EffectsProcessingRequest, EffectsProcessingResponse,
    EffectsProcessingResult, EffectsCatalogItem, EffectsPreset
)
from tasks.effects_processing import process_audio_with_effects
from services.storage_service import get_storage_service, is_storage_enabled, get_storage_type
from services.effects_processor import get_effects_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/effects", tags=["Effects Processing"])


@router.post("/process", response_model=EffectsProcessingResponse)
async def process_audio_with_effects_route(request: EffectsProcessingRequest):
    """
    Process audio file with custom effects chains for individual stems
    
    This endpoint:
    1. Loads audio from storage
    2. Separates into stems (vocals, drums, bass, other) 
    3. Applies custom effects chains to each stem
    4. Mixes stems back together with master effects
    5. Saves final processed audio
    
    The processing is performed asynchronously using Celery.
    Results are delivered via callback URL if provided.
    """
    logger.info(f"Received effects processing request: {request.storage_path}")
    
    if not is_storage_enabled():
        logger.error("Storage is not properly configured")
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        # Validate request fields
        if not request.storage_path:
            logger.error("Missing required field: storage_path")
            raise HTTPException(status_code=422, detail="storage_path is required")
        
        if not request.effects_config:
            logger.error("Missing required field: effects_config")
            raise HTTPException(status_code=422, detail="effects_config is required")
            
        if not request.effects_config.stem_chains:
            logger.error("effects_config must contain at least one stem chain")
            raise HTTPException(status_code=422, detail="effects_config must contain at least one stem chain")
        
        logger.info(f"Processing effects request for storage path: {request.storage_path}")
        
        storage = get_storage_service()
        
        # Check if file exists in storage
        if not storage.file_exists(request.storage_path):
            logger.error(f"File not found in storage: {request.storage_path}")
            raise HTTPException(status_code=404, detail=f"File not found in storage: {request.storage_path}")
        
        # Validate effects configuration
        processor = get_effects_processor()
        if not processor.is_available():
            logger.error("Effects processing is not available (pedalboard not installed)")
            raise HTTPException(status_code=503, detail="Effects processing is not available")
        
        # Validate the effects configuration
        is_valid, warnings = processor.validate_configuration(request.effects_config)
        if not is_valid:
            logger.error(f"Invalid effects configuration: {warnings}")
            raise HTTPException(status_code=422, detail=f"Invalid effects configuration: {'; '.join(warnings)}")
        
        if warnings:
            logger.warning(f"Effects configuration warnings: {warnings}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        logger.info(f"Generated task ID: {task_id} for effects processing: {request.storage_path}")
        
        # Queue async processing
        celery_task = process_audio_with_effects.delay(
            task_id=task_id,
            storage_path=request.storage_path,
            effects_config=request.effects_config.model_dump(),
            callback_url=request.callback_url,
            user_id=request.user_id,
            output_format=request.output_format,
            separate_stems=request.separate_stems
        )
        
        storage_type = get_storage_type()
        effects_count = sum(len(chain.effects) for chain in request.effects_config.stem_chains)
        effects_count += len(request.effects_config.master_chain.effects)
        
        logger.info(f"Queued effects processing: {request.storage_path} (task: {task_id}, effects: {effects_count}, storage: {storage_type.value})")
        
        # Estimate completion time based on effect complexity
        estimated_time = min(60 + (effects_count * 10), 1800)  # 1 min base + 10s per effect, max 30 min
        
        return EffectsProcessingResponse(
            task_id=task_id,
            status="processing",
            message=f"Effects processing started with {effects_count} effects from {storage_type.value} storage",
            storage_type=storage_type.value,
            estimated_completion_time=estimated_time
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing effects request: {e}")
        logger.error(f"Request data: {request}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/catalog")
async def get_effects_catalog():
    """
    Get catalog of available effects with their parameters and specifications
    
    Returns detailed information about each available effect including:
    - Effect type and name
    - Category (dynamics, eq_filter, time_based, etc.)
    - Description and complexity level
    - Parameter specifications with ranges and defaults
    """
    try:
        processor = get_effects_processor()
        
        if not processor.is_available():
            logger.warning("Effects processor not available, returning empty catalog")
            return {"effects": [], "available": False, "message": "Effects processing not available"}
        
        effects_catalog = processor.get_supported_effects()
        
        logger.info(f"Retrieved effects catalog with {len(effects_catalog)} effects")
        
        return {
            "effects": effects_catalog,
            "available": True,
            "total_effects": len(effects_catalog),
            "categories": list(set(effect.get("category", "unknown") for effect in effects_catalog))
        }
        
    except Exception as e:
        logger.error(f"Error retrieving effects catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve effects catalog: {str(e)}")


@router.get("/presets")
async def get_effects_presets():
    """
    Get available effects presets for common audio processing scenarios
    
    Returns a collection of pre-configured effect chains for:
    - Vocal enhancement
    - Drum processing
    - Master bus processing
    - Creative effects
    """
    try:
        # Built-in preset configurations
        presets = [
            {
                "name": "Vocal Enhancement",
                "description": "Professional vocal processing chain with compression, EQ, and reverb",
                "category": "vocals",
                "complexity": "medium",
                "tags": ["vocals", "professional", "compression", "reverb"],
                "config": {
                    "stem_chains": [
                        {
                            "stem": "vocals",
                            "effects": [
                                {
                                    "id": "vocal_comp",
                                    "type": "compressor",
                                    "name": "Vocal Compressor", 
                                    "parameters": {
                                        "threshold_db": -18.0,
                                        "ratio": 3.0,
                                        "attack_ms": 5.0,
                                        "release_ms": 150.0,
                                        "knee_db": 2.0,
                                        "makeup_gain_db": 2.0
                                    },
                                    "bypass": False,
                                    "order": 0
                                },
                                {
                                    "id": "vocal_eq",
                                    "type": "high_shelf",
                                    "name": "Vocal Brightness",
                                    "parameters": {
                                        "cutoff_frequency_hz": 3000.0,
                                        "gain_db": 2.0,
                                        "q": 0.7
                                    },
                                    "bypass": False,
                                    "order": 1
                                },
                                {
                                    "id": "vocal_reverb",
                                    "type": "reverb",
                                    "name": "Vocal Reverb",
                                    "parameters": {
                                        "room_size": 0.3,
                                        "damping": 0.6,
                                        "wet_level": 0.15,
                                        "dry_level": 1.0,
                                        "width": 0.8
                                    },
                                    "bypass": False,
                                    "order": 2
                                }
                            ],
                            "volume": 1.1,
                            "pan": 0.0,
                            "mute": False,
                            "solo": False
                        }
                    ],
                    "master_chain": {
                        "effects": [],
                        "volume": 1.0
                    }
                }
            },
            {
                "name": "Punchy Drums",
                "description": "Dynamic drum processing with compression and transient enhancement",
                "category": "drums",
                "complexity": "medium",
                "tags": ["drums", "compression", "punch", "dynamics"],
                "config": {
                    "stem_chains": [
                        {
                            "stem": "drums",
                            "effects": [
                                {
                                    "id": "drum_gate",
                                    "type": "gate",
                                    "name": "Drum Gate",
                                    "parameters": {
                                        "threshold_db": -35.0,
                                        "ratio": 8.0,
                                        "attack_ms": 1.0,
                                        "release_ms": 50.0
                                    },
                                    "bypass": False,
                                    "order": 0
                                },
                                {
                                    "id": "drum_comp",
                                    "type": "compressor",
                                    "name": "Drum Compressor",
                                    "parameters": {
                                        "threshold_db": -15.0,
                                        "ratio": 4.0,
                                        "attack_ms": 3.0,
                                        "release_ms": 80.0,
                                        "knee_db": 1.0,
                                        "makeup_gain_db": 3.0
                                    },
                                    "bypass": False,
                                    "order": 1
                                }
                            ],
                            "volume": 1.0,
                            "pan": 0.0,
                            "mute": False,
                            "solo": False
                        }
                    ],
                    "master_chain": {
                        "effects": [],
                        "volume": 1.0
                    }
                }
            },
            {
                "name": "Master Bus Glue",
                "description": "Gentle master bus compression and limiting for cohesive mix",
                "category": "master",
                "complexity": "simple",
                "tags": ["master", "glue", "compression", "limiting"],
                "config": {
                    "stem_chains": [],
                    "master_chain": {
                        "effects": [
                            {
                                "id": "master_comp",
                                "type": "compressor",
                                "name": "Master Compressor",
                                "parameters": {
                                    "threshold_db": -12.0,
                                    "ratio": 2.5,
                                    "attack_ms": 15.0,
                                    "release_ms": 200.0,
                                    "knee_db": 3.0,
                                    "makeup_gain_db": 1.0
                                },
                                "bypass": False,
                                "order": 0
                            },
                            {
                                "id": "master_limiter",
                                "type": "limiter",
                                "name": "Master Limiter",
                                "parameters": {
                                    "threshold_db": -0.5,
                                    "release_ms": 50.0
                                },
                                "bypass": False,
                                "order": 1
                            }
                        ],
                        "volume": 0.98
                    }
                }
            },
            {
                "name": "Creative Distortion",
                "description": "Artistic distortion and filtering for creative effect processing",
                "category": "creative",
                "complexity": "advanced",
                "tags": ["distortion", "creative", "artistic", "filtering"],
                "config": {
                    "stem_chains": [
                        {
                            "stem": "other",
                            "effects": [
                                {
                                    "id": "creative_dist",
                                    "type": "distortion",
                                    "name": "Creative Distortion",
                                    "parameters": {
                                        "drive_db": 15.0
                                    },
                                    "bypass": False,
                                    "order": 0
                                },
                                {
                                    "id": "creative_filter",
                                    "type": "ladder_filter",
                                    "name": "Creative Filter",
                                    "parameters": {
                                        "cutoff_hz": 2000.0,
                                        "resonance": 0.3,
                                        "drive": 1.2,
                                        "mode": "LPF12"
                                    },
                                    "bypass": False,
                                    "order": 1
                                }
                            ],
                            "volume": 0.8,
                            "pan": 0.0,
                            "mute": False,
                            "solo": False
                        }
                    ],
                    "master_chain": {
                        "effects": [],
                        "volume": 1.0
                    }
                }
            }
        ]
        
        logger.info(f"Retrieved {len(presets)} effects presets")
        
        return {
            "presets": presets,
            "total_presets": len(presets),
            "categories": list(set(preset["category"] for preset in presets))
        }
        
    except Exception as e:
        logger.error(f"Error retrieving effects presets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve effects presets: {str(e)}")


@router.get("/status")
async def get_effects_status():
    """
    Get current status of the effects processing system
    
    Returns information about:
    - Effects processor availability
    - Supported effects count
    - System capabilities
    """
    try:
        processor = get_effects_processor()
        is_available = processor.is_available()
        
        status_info = {
            "available": is_available,
            "storage_enabled": is_storage_enabled(),
            "storage_type": get_storage_type().value if is_storage_enabled() else None
        }
        
        if is_available:
            effects_catalog = processor.get_supported_effects()
            status_info.update({
                "supported_effects": len(effects_catalog),
                "effect_categories": list(set(effect.get("category", "unknown") for effect in effects_catalog)),
                "message": "Effects processing is available and ready"
            })
        else:
            status_info.update({
                "supported_effects": 0,
                "effect_categories": [],
                "message": "Effects processing is not available (pedalboard not installed)"
            })
        
        logger.info(f"Effects status check: available={is_available}")
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error checking effects status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check effects status: {str(e)}")