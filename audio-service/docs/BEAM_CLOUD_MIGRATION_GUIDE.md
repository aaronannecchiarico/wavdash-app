# Beam Cloud / Beta9 Migration Guide for Audio Feature Extraction Service

## Executive Summary

This document analyzes the potential migration of our FastAPI + Celery audio feature extraction service to Beam Cloud's Beta9 platform. Beta9 is an open-source, serverless GPU runtime that could provide significant cost savings through its pay-per-millisecond model, automatic scaling, and serverless architecture.

**Key Findings:**
- **Cost Savings Potential**: 60-80% reduction in compute costs due to true serverless scale-to-zero
- **Performance Improvements**: Sub-second cold starts, automatic GPU/CPU scaling
- **Simplified Infrastructure**: No Redis/Celery management, built-in task queuing
- **Migration Complexity**: Moderate - requires code refactoring but preserves core logic

---

## Current Architecture Analysis

### Current Stack
- **API**: FastAPI (main.py)
- **Task Queue**: Celery with Redis broker
- **Workers**: Separate Celery worker processes
- **Storage**: Local filesystem or Cloudflare R2
- **Compute**: Fixed infrastructure with manual scaling

### Current Processing Pipeline
1. **Audio Feature Extraction** (`services/audio_feature_extraction.py`)
   - Librosa-based audio analysis (MFCC, Chroma, Spectral features)
   - BPM detection with ensemble methods
   - Chunked processing for files >60s

2. **AI Stem Separation** (`tasks/audio_processing.py`)
   - Demucs model-based separation
   - GPU-accelerated processing (CUDA/MPS)
   - Resource-intensive workload

3. **Tempo Processing** (`tasks/tempo_processing.py`)
   - Advanced tempo manipulation
   - Real-time audio effects using Pedalboard

4. **Storage Processing** (`tasks/storage_processing.py`)
   - Laravel integration callbacks
   - User-based folder structure

### Current Resource Requirements
- **Python Dependencies**: PyTorch (2.6GB+), Demucs models (500MB-2GB)
- **GPU Requirements**: CUDA/MPS for AI models
- **Memory**: 4-8GB for model loading, varies by workload
- **Processing Time**: 30s-25min per job depending on complexity

---

## Beam Cloud / Beta9 Platform Analysis

### Core Capabilities
- **Serverless Container Runtime**: Sub-second container launches
- **Multi-compute Support**: CPU and GPU workloads (RTX 4090, H100)
- **Auto-scaling**: Scale to thousands of containers, automatic scale-to-zero
- **Python-First**: Decorator-based deployment model
- **Distributed Computing**: Built-in parallelization and concurrency

### Programming Models Available
1. **Function Decorators** (`@beam.function`)
   - Isolated code execution in secure sandboxes
   - Perfect for feature extraction tasks

2. **Endpoint Decorators** (`@beam.endpoint`)
   - REST API endpoints with automatic scaling
   - Replace FastAPI routes

3. **Task Decorators** (`@beam.task`)
   - Background job processing
   - Replace Celery tasks

### Deployment Options
- **Self-hosted Beta9**: Free, open-source
- **Managed Beam Cloud**: Pay-per-millisecond pricing

---

## Cost Analysis and Savings Potential

### Current Cost Structure (Estimated)
Assuming typical VPS/cloud deployment:

- **Always-On Infrastructure**: $200-500/month
  - API server: $50-100/month
  - Redis instance: $20-50/month
  - Worker servers (2-3): $100-300/month
  - GPU instances: $30-100/month (when needed)

- **Utilization Issues**:
  - Infrastructure runs 24/7 regardless of usage
  - Peak capacity provisioned for occasional high loads
  - GPU resources often idle between jobs

### Beam Cloud Cost Model
- **Pay-per-millisecond**: Only pay for actual compute time
- **Automatic scaling**: No idle resource costs
- **GPU on-demand**: GPU costs only when processing AI workloads

### Projected Savings
Based on typical audio processing service usage patterns:

- **Low-utilization scenarios** (< 20% average usage): **70-80% savings**
- **Medium-utilization scenarios** (20-50% average usage): **40-60% savings**
- **High-utilization scenarios** (> 50% average usage): **20-30% savings**

**Example Cost Calculation:**
- Current: $300/month for always-on infrastructure
- Beam Cloud: ~$60-120/month for actual usage (assuming 15-30% utilization)
- **Savings: $180-240/month (60-80% reduction)**

*Note: Exact pricing unavailable without Beam Cloud account. Estimates based on industry standards.*

---

## Migration Strategy

### Phase 1: Proof of Concept (2-3 weeks)

#### Step 1: Set Up Beta9 Development Environment
```bash
# Install Beta9 SDK
pip install beta9

# Initialize project
beta9 init audio-processing

# Set up basic configuration
beta9 config
```

#### Step 2: Migrate Core Audio Feature Extraction
Convert the simplest task first - basic audio feature extraction:

```python
import beta9
from beta9 import function, Image

# Define container image with audio processing dependencies
audio_image = Image().add_python_packages([
    "librosa>=0.10.0",
    "soundfile>=0.12.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0"
])

@function(
    image=audio_image,
    cpu=2,
    memory="4Gi"
)
def extract_audio_features(audio_file_path: str, user_id: str = None):
    """
    Migrate from services/audio_feature_extraction.py
    Convert existing feature extraction logic
    """
    # Import existing feature extraction logic
    from services.audio_feature_extraction import AudioFeatureExtractor
    
    extractor = AudioFeatureExtractor()
    return extractor.extract_features(audio_file_path, user_id)
```

#### Step 3: Test Basic Workflow
- Deploy single function to Beta9
- Compare performance and costs
- Validate output compatibility with Laravel integration

### Phase 2: Core Task Migration (3-4 weeks)

#### Step 1: Migrate AI/GPU Workloads
Convert Demucs stem separation to GPU-enabled Beta9 functions:

```python
# GPU-enabled image for AI models
ai_image = Image().add_python_packages([
    "torch>=2.6.0",
    "torchaudio>=2.6.0",
    "demucs>=4.0.0"
])

@function(
    image=ai_image,
    gpu="rtx4090",  # or "h100" for high-end workloads
    memory="16Gi",
    timeout=1800  # 30 min timeout
)
def separate_audio_stems(audio_file_path: str, user_id: str = None):
    """
    Migrate from tasks/audio_processing.py
    Convert Demucs separation logic
    """
    # Import existing stem separation logic
    from tasks.audio_processing import separate_stems_task
    
    return separate_stems_task.apply(args=[audio_file_path, user_id]).get()
```

#### Step 2: Migrate Tempo Processing
```python
@function(
    image=audio_image,
    cpu=4,
    memory="8Gi"
)
def process_tempo_effects(input_path: str, effects_config: dict, user_id: str = None):
    """
    Migrate from tasks/tempo_processing.py
    Convert Pedalboard effects processing
    """
    # Import existing tempo processing logic
    from tasks.tempo_processing import process_tempo_with_effects
    
    return process_tempo_with_effects.apply(args=[input_path, effects_config, user_id]).get()
```

#### Step 3: Replace Task Queue Logic
Convert Celery-style callback handling:

```python
import httpx

@function(image=audio_image)
def process_storage_audio_with_callback(storage_path: str, callback_url: str, user_id: str = None):
    """
    Migrate from tasks/storage_processing.py
    Maintain Laravel integration callbacks
    """
    try:
        # Process audio
        features = extract_audio_features(storage_path, user_id)
        
        # Send callback (maintain existing callback format)
        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json={
                "status": "completed",
                "analysis_summary": features,
                "user_id": user_id
            })
            
    except Exception as e:
        # Error callback
        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json={
                "status": "failed",
                "error": str(e),
                "user_id": user_id
            })
```

### Phase 3: API Layer Migration (2-3 weeks)

#### Step 1: Convert FastAPI Routes to Beta9 Endpoints
```python
from beta9 import endpoint
from pydantic import BaseModel

class FeatureExtractionRequest(BaseModel):
    storage_path: str
    callback_url: str
    user_id: str = None

@endpoint(
    image=audio_image,
    cpu=1,
    memory="2Gi"
)
def extract_features_endpoint(request: FeatureExtractionRequest):
    """
    Replace routes/storage.py endpoints
    """
    # Async task dispatch to feature extraction function
    job = extract_audio_features.map([request.storage_path], user_id=request.user_id)
    
    return {
        "job_id": job.id,
        "status": "processing",
        "message": "Feature extraction started"
    }
```

#### Step 2: Implement Health Checks and Status Endpoints
```python
@endpoint(image=Image())
def health_check():
    """
    Replace routes/health.py
    """
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@endpoint(image=Image())
def job_status(job_id: str):
    """
    Replace routes/tasks.py job status checking
    """
    # Beta9 provides job status tracking
    job = beta9.get_job(job_id)
    return {
        "job_id": job_id,
        "status": job.status,
        "result": job.result if job.complete else None
    }
```

### Phase 4: Storage Integration (1-2 weeks)

#### Step 1: Integrate with Current Storage Service
```python
from beta9 import Image

# Create shared storage image
storage_image = Image().add_python_packages([
    "boto3>=1.26.0",  # For R2/S3 storage
    "httpx==0.25.2"   # For HTTP requests
])

@function(image=storage_image)
def storage_aware_processing(storage_path: str, user_id: str = None):
    """
    Integrate with services/storage_service.py
    """
    from services.storage_service import StorageService
    
    storage = StorageService()
    
    # Download from storage
    local_path = storage.download_file(storage_path)
    
    # Process
    result = extract_audio_features(local_path, user_id)
    
    # Upload result
    result_path = storage.upload_processed_result(result, user_id)
    
    return {"result_path": result_path, "analysis": result}
```

### Phase 5: Production Deployment (1-2 weeks)

#### Step 1: Environment Configuration
```python
# beam.yaml - Beta9 configuration
name: audio-processing-service
python_version: "3.11"

resources:
  default_cpu: 2
  default_memory: "4Gi"
  default_timeout: 3600

secrets:
  - REDIS_URL
  - STORAGE_TYPE  
  - LOCAL_STORAGE_PATH
  - CLOUDFLARE_R2_ACCESS_KEY
  - CLOUDFLARE_R2_SECRET_KEY
```

#### Step 2: Monitoring and Observability
```python
import structlog

@function(image=audio_image)
def monitored_processing(audio_path: str):
    """
    Add monitoring and logging
    """
    logger = structlog.get_logger()
    
    logger.info("Processing started", audio_path=audio_path)
    
    try:
        result = extract_audio_features(audio_path)
        logger.info("Processing completed", result_size=len(str(result)))
        return result
    except Exception as e:
        logger.error("Processing failed", error=str(e))
        raise
```

---

## Migration Implementation Guide

### Prerequisites
1. **Beta9/Beam Cloud Account Setup**
   - Sign up for Beam Cloud account
   - Install Beta9 CLI: `pip install beta9`
   - Configure authentication: `beta9 auth`

2. **Development Environment**
   - Python 3.11+ (Beta9 compatible)
   - Docker (for container image builds)
   - Access to current codebase and dependencies

### Detailed Migration Steps

#### 1. Project Structure Reorganization
```
audio-processing-service/
├── beam/
│   ├── functions/           # Beta9 function definitions
│   │   ├── feature_extraction.py
│   │   ├── stem_separation.py
│   │   ├── tempo_processing.py
│   │   └── storage_processing.py
│   ├── endpoints/          # Beta9 API endpoints
│   │   ├── health.py
│   │   ├── audio.py
│   │   └── storage.py
│   ├── images/             # Container image definitions
│   │   ├── audio_base.py
│   │   ├── ai_models.py
│   │   └── storage.py
│   └── utils/              # Shared utilities
│       ├── storage.py
│       └── callbacks.py
├── legacy/                 # Keep current FastAPI/Celery code
│   ├── main.py
│   ├── celery_app.py
│   └── ...
├── beam.yaml              # Beta9 configuration
└── requirements-beta9.txt # Beta9-specific dependencies
```

#### 2. Code Conversion Patterns

**From Celery Task to Beta9 Function:**
```python
# BEFORE (Celery)
from celery_app import celery_app

@celery_app.task(bind=True)
def extract_features_task(self, audio_path, user_id=None):
    try:
        # processing logic
        return result
    except Exception as exc:
        self.retry(countdown=60, exc=exc)

# AFTER (Beta9)
from beta9 import function

@function(cpu=2, memory="4Gi", timeout=1800, retries=3)
def extract_features(audio_path: str, user_id: str = None):
    # same processing logic
    return result
```

**From FastAPI Route to Beta9 Endpoint:**
```python
# BEFORE (FastAPI)
from fastapi import APIRouter
from celery import current_app

router = APIRouter()

@router.post("/extract")
async def extract_endpoint(request: ExtractRequest):
    task = extract_features_task.delay(request.path, request.user_id)
    return {"task_id": task.id}

# AFTER (Beta9)
from beta9 import endpoint

@endpoint(cpu=1, memory="2Gi")
def extract_endpoint(request: ExtractRequest):
    job = extract_features.spawn(request.path, request.user_id)
    return {"job_id": job.id}
```

#### 3. Container Image Management

**Create Optimized Images:**
```python
# beam/images/audio_base.py
from beta9 import Image

# Base audio processing image
audio_base = Image(
    python_version="3.11"
).add_python_packages([
    "librosa>=0.10.0",
    "soundfile>=0.12.0", 
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "pydantic>=2.6.0"
]).add_commands([
    "apt-get update && apt-get install -y ffmpeg"
])

# AI models image (for GPU workloads)
ai_models = Image(
    python_version="3.11"
).add_python_packages([
    "torch>=2.6.0",
    "torchaudio>=2.6.0", 
    "demucs>=4.0.0"
]).add_commands([
    "apt-get update && apt-get install -y ffmpeg"
])
```

#### 4. Storage Integration Strategy

**Maintain Current Storage Abstraction:**
```python
# beam/utils/storage.py
from services.storage_service import StorageService

class Beta9StorageAdapter:
    def __init__(self):
        self.storage_service = StorageService()
    
    def download_and_process(self, storage_path: str, processor_func, **kwargs):
        """
        Download from storage, process, upload results
        """
        # Download to temporary location
        local_path = self.storage_service.download_file(storage_path)
        
        # Process using Beta9 function
        result = processor_func(local_path, **kwargs)
        
        # Upload processed result
        result_path = self.storage_service.upload_processed_result(result, kwargs.get('user_id'))
        
        # Cleanup temporary files
        os.unlink(local_path)
        
        return {"result_path": result_path, "data": result}
```

#### 5. Laravel Integration Compatibility

**Maintain Callback Structure:**
```python
# beam/utils/callbacks.py
import httpx
from typing import Optional

class LaravelCallbackHandler:
    @staticmethod
    async def send_completion_callback(
        callback_url: str,
        status: str,
        analysis_summary: dict,
        user_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Maintain existing Laravel callback format
        """
        payload = {
            "status": status,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if status == "completed":
            payload["analysis_summary"] = analysis_summary
        elif status == "failed":
            payload["error"] = error
            
        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, json=payload)
            return response.status_code == 200
```

#### 6. Testing Strategy

**Create Beta9-Compatible Tests:**
```python
# tests/test_beta9_functions.py
import pytest
from beam.functions.feature_extraction import extract_audio_features

def test_feature_extraction_beta9():
    """
    Test Beta9 function locally before deployment
    """
    # Beta9 functions can be tested locally
    result = extract_audio_features.local("test_audio.wav", user_id="test_user")
    
    assert "tempo" in result
    assert "key" in result
    assert result["duration"] > 0

# Integration tests with Laravel callbacks
@pytest.mark.asyncio
async def test_callback_integration():
    """
    Test Laravel callback compatibility
    """
    from beam.utils.callbacks import LaravelCallbackHandler
    
    # Mock callback URL
    callback_url = "http://localhost:8000/api/audio-processing/callback"
    
    # Test callback sending
    success = await LaravelCallbackHandler.send_completion_callback(
        callback_url=callback_url,
        status="completed",
        analysis_summary={"tempo": 120, "key": "C"},
        user_id="test_user"
    )
    
    assert success
```

---

## Risk Assessment and Mitigation

### Technical Risks

1. **Container Build Times**
   - **Risk**: Large ML models increase build times
   - **Mitigation**: Use layered images, pre-built base images with common dependencies

2. **Cold Start Performance**
   - **Risk**: Model loading adds latency to cold starts
   - **Mitigation**: Beta9's sub-second starts + model caching strategies

3. **GPU Availability**
   - **Risk**: GPU instances may not be immediately available
   - **Mitigation**: Graceful fallback to CPU processing, queue management

4. **Vendor Lock-in**
   - **Risk**: Beta9-specific deployment patterns
   - **Mitigation**: Open-source Beta9 allows self-hosting, standard container patterns

### Business Risks

1. **Migration Complexity**
   - **Risk**: Significant development time investment
   - **Mitigation**: Phased migration approach, parallel operation during transition

2. **Performance Changes**
   - **Risk**: Different performance characteristics
   - **Mitigation**: Thorough testing, gradual rollout with monitoring

3. **Cost Predictability**
   - **Risk**: Variable usage patterns affect costs
   - **Mitigation**: Usage monitoring, cost alerting, fallback to fixed infrastructure if needed

### Mitigation Strategies

1. **Gradual Migration**
   - Keep existing FastAPI/Celery infrastructure running
   - Migrate one workload type at a time
   - Use feature flags to route traffic between old/new systems

2. **Comprehensive Testing**
   - Local testing of Beta9 functions
   - Staging environment with Beta9
   - Load testing before production migration

3. **Monitoring and Alerting**
   - Cost monitoring dashboards
   - Performance metrics comparison
   - Error rate tracking across both systems

4. **Rollback Plan**
   - Keep legacy code available
   - Database/storage compatibility maintained
   - Quick switching mechanism between platforms

---

## Timeline and Resource Requirements

### Development Timeline: 8-12 weeks total

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: POC | 2-3 weeks | Basic function migration, cost validation |
| Phase 2: Core Tasks | 3-4 weeks | All major processing tasks migrated |
| Phase 3: API Layer | 2-3 weeks | REST API endpoints, Laravel integration |
| Phase 4: Storage | 1-2 weeks | Storage service integration |
| Phase 5: Production | 1-2 weeks | Deployment, monitoring, testing |

### Resource Requirements

**Development Team:**
- 1 Senior Backend Developer (full-time)
- 1 DevOps Engineer (50% time)
- 1 QA Engineer (25% time for testing)

**Infrastructure:**
- Beta9/Beam Cloud development account
- Staging environment access
- Performance testing environment

**Key Milestones:**
- Week 3: POC completed, cost savings validated
- Week 7: Core functionality migrated and tested
- Week 10: Full API compatibility achieved  
- Week 12: Production deployment complete

---

## Conclusion and Recommendations

### Key Benefits of Migration

1. **Significant Cost Savings**: 60-80% reduction in infrastructure costs through serverless scale-to-zero
2. **Improved Scalability**: Automatic scaling to handle traffic spikes without manual intervention  
3. **Simplified Operations**: No Redis/Celery management, reduced infrastructure complexity
4. **Better Performance**: Sub-second cold starts, optimized GPU utilization

### Recommended Approach

1. **Start with Phase 1 POC** to validate cost savings and technical feasibility
2. **Measure actual usage patterns** during POC to refine cost projections
3. **Maintain parallel systems** during migration to reduce risk
4. **Focus on high-impact, low-risk workloads first** (basic feature extraction)
5. **Save complex AI workloads for later phases** once patterns are established

### Success Criteria

- **Cost Reduction**: Achieve >50% infrastructure cost savings
- **Performance Maintenance**: No degradation in processing times
- **Reliability**: Maintain >99% uptime during migration
- **Laravel Compatibility**: Zero changes required to Laravel integration

The migration to Beta9/Beam Cloud represents a strategic opportunity to modernize the audio processing infrastructure while achieving significant cost savings. The serverless model aligns well with the variable nature of audio processing workloads, and the Python-first approach minimizes migration complexity.

**Next Step**: Proceed with Phase 1 POC to validate assumptions and measure actual cost savings before committing to full migration.