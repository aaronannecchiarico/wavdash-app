# Google Cloud Run Implementation Guide for Audio Feature Extraction Service

## Architecture Decision Summary

After analyzing both the Beam Cloud and Comprehensive Cost Optimization guides, **Google Cloud Run** emerges as the optimal serverless solution for the following reasons:

### Why Google Cloud Run?

✅ **Minimal Migration Effort**: Existing FastAPI application requires only containerization - no code rewriting  
✅ **Established Platform**: Mature Google service with extensive documentation and proven reliability  
✅ **Native GPU Support**: NVIDIA L4 GPUs with 5-second cold starts for stem separation  
✅ **Laravel Integration**: Standard HTTP callbacks work unchanged - no integration complexity  
✅ **Cost Effectiveness**: True serverless scale-to-zero pricing with generous free tier  
✅ **1-Hour Timeout**: Suitable for complex audio processing tasks  
✅ **Transparent Pricing**: Clear, predictable cost structure

**Projected Savings**: 70-85% reduction in infrastructure costs ($300/month → $45-90/month)

---

## Target Architecture

```mermaid
graph TD
    A[Laravel App] -->|HTTP Request| B[Cloud Run API Service]
    B -->|Queue Job| C[Upstash Redis]
    C -->|Process| D[Cloud Run Worker - CPU]
    C -->|Process GPU| E[Cloud Run Worker - GPU]
    D -->|Results| F[Cloud Storage]
    E -->|Results| F[Cloud Storage]
    D -->|Callback| A
    E -->|Callback| A
    
    G[Cloud Run Services] --> H[CPU Processing]
    G --> I[GPU Processing - L4]
    
    H --> J[Feature Extraction]
    H --> K[Tempo Processing]
    I --> L[Stem Separation - Demucs]
```

**Key Components:**
- **API Service**: FastAPI containerized on Cloud Run (always available, minimal cost)
- **CPU Workers**: Audio feature extraction, tempo processing
- **GPU Workers**: AI stem separation using NVIDIA L4 GPUs
- **Queue**: Upstash Redis (serverless, pay-per-request)
- **Storage**: Google Cloud Storage (pay-per-use)
- **Laravel Integration**: Standard HTTP callbacks (no changes needed)

---

## Prerequisites

### Local Development Environment
```bash
# Required tools
- Docker Desktop 4.0+
- Google Cloud CLI (gcloud)
- Python 3.11+
- Git

# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### Google Cloud Setup
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Set default region (choose closest to your users)
gcloud config set run/region us-central1

# Create project variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
```

---

## Phase 1: Local Development Setup

### Step 1: Containerize Existing Application

Create optimized Docker configuration:

**Dockerfile**
```dockerfile
# Multi-stage build for optimal size
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

**Docker Compose for Local Development**
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - STORAGE_TYPE=local
      - LOCAL_STORAGE_PATH=/app/storage
      - DEBUG=true
    volumes:
      - ./storage:/app/storage
      - .:/app
    depends_on:
      - redis
    command: uvicorn main:app --host 0.0.0.0 --port 8080 --reload

  worker-cpu:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - STORAGE_TYPE=local
      - LOCAL_STORAGE_PATH=/app/storage
      - WORKER_TYPE=cpu
    volumes:
      - ./storage:/app/storage
      - .:/app
    depends_on:
      - redis
    command: python start_worker.py

  worker-gpu:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - STORAGE_TYPE=local
      - LOCAL_STORAGE_PATH=/app/storage
      - WORKER_TYPE=gpu
    volumes:
      - ./storage:/app/storage
      - .:/app
    depends_on:
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: python start_worker.py

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Step 2: Modify Application for Cloud Run

**Update main.py for Cloud Run compatibility:**

```python
# main.py - Cloud Run optimizations
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
from contextlib import asynccontextmanager

from config import settings
from routes.tempo_processing import router as tempo_router
from routes.audio_processing import router as audio_router
from routes.storage import router as storage_router
from routes.tasks import router as tasks_router
from routes.health import router as health_router
from routes.effects_processing import router as effects_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting audio processing microservice on Cloud Run")
    yield
    logging.info("Shutting down audio processing microservice")

app = FastAPI(
    title="Audio Processing Microservice",
    description="FastAPI microservice for audio feature extraction and stem separation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (remove migration router for production)
app.include_router(health_router)
app.include_router(audio_router)
app.include_router(storage_router)
app.include_router(tasks_router)
app.include_router(tempo_router)
app.include_router(effects_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed logging"""
    request_body = None
    try:
        request_body = await request.body()
        if request_body:
            request_body = request_body.decode('utf-8')
    except Exception:
        request_body = "Unable to read request body"
    
    logging.error(f"422 Validation Error on {request.method} {request.url}")
    logging.error(f"Request body: {request_body}")
    logging.error(f"Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": request_body if request_body != "Unable to read request body" else None
        }
    )

if __name__ == "__main__":
    # Cloud Run sets PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1  # Single worker for Cloud Run
    )
```

### Step 3: Create Upstash Redis Configuration

**Setup serverless Redis:**

```bash
# Sign up for Upstash at https://upstash.com
# Create Redis database (choose closest region to your Cloud Run deployment)
# Get connection details

# Add to environment variables
export UPSTASH_REDIS_URL="rediss://username:password@endpoint:port"
```

**Update Redis configuration:**

```python
# config/redis_config.py
import os
import redis
from typing import Optional

class RedisConfig:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.is_upstash = "upstash" in self.redis_url
        
    def get_client(self) -> redis.Redis:
        """Get Redis client configured for environment"""
        if self.is_upstash:
            # Upstash Redis configuration
            return redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        else:
            # Local Redis configuration
            return redis.from_url(self.redis_url, decode_responses=True)

redis_client = RedisConfig().get_client()
```

---

## Phase 2: Local Testing Environment

### Step 1: Local Development Testing

**Build and test locally:**

```bash
# Build the container
docker build -t audio-processor:local .

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Test API health
curl http://localhost:8080/health

# Test feature extraction endpoint
curl -X POST http://localhost:8080/storage/extract-features \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "/app/storage/test_audio.wav",
    "callback_url": "http://localhost:8080/test-callback",
    "user_id": "test_user"
  }'
```

### Step 2: Local GPU Testing (if available)

**Test GPU workers locally:**

```bash
# Check GPU availability
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Start with GPU support
docker-compose -f docker-compose.dev.yml up worker-gpu

# Test stem separation
curl -X POST http://localhost:8080/audio/separate-stems \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "/app/storage/test_audio.wav",
    "callback_url": "http://localhost:8080/test-callback",
    "user_id": "test_user"
  }'
```

### Step 3: Comprehensive Test Suite

**Create test suite for Cloud Run:**

```python
# tests/test_cloud_run.py
import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
from main import app

class TestCloudRunIntegration:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_feature_extraction_endpoint(self, client):
        """Test feature extraction API"""
        payload = {
            "storage_path": "test_audio.wav",
            "callback_url": "http://localhost:8080/test-callback",
            "user_id": "test_user"
        }
        response = client.post("/storage/extract-features", json=payload)
        assert response.status_code in [200, 202]  # Success or Accepted
    
    def test_stem_separation_endpoint(self, client):
        """Test stem separation API"""
        payload = {
            "storage_path": "test_audio.wav", 
            "callback_url": "http://localhost:8080/test-callback",
            "user_id": "test_user"
        }
        response = client.post("/audio/separate-stems", json=payload)
        assert response.status_code in [200, 202]
    
    @pytest.mark.asyncio
    async def test_callback_functionality(self):
        """Test Laravel callback integration"""
        async with httpx.AsyncClient() as client:
            # Mock callback payload
            callback_data = {
                "status": "completed",
                "analysis_summary": {
                    "tempo": 120.0,
                    "key": "C",
                    "duration": 180.5
                },
                "user_id": "test_user"
            }
            
            # Test callback (would normally go to Laravel)
            response = await client.post(
                "http://localhost:8080/test-callback",
                json=callback_data
            )
            assert response.status_code == 200
    
    def test_tempo_processing_endpoint(self, client):
        """Test tempo processing API"""
        payload = {
            "input_path": "test_audio.wav",
            "effects_config": {
                "tempo_factor": 1.2,
                "pitch_shift": 2
            },
            "callback_url": "http://localhost:8080/test-callback",
            "user_id": "test_user"
        }
        response = client.post("/tempo/process-tempo", json=payload)
        assert response.status_code in [200, 202]
```

**Run local tests:**

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/test_cloud_run.py -v

# Run with coverage
pytest tests/test_cloud_run.py --cov=. --cov-report=html
```

---

## Phase 3: Cloud Deployment

### Step 1: Setup Google Cloud Project

**Create and configure project:**

```bash
# Create new project (or use existing)
export PROJECT_ID="your-audio-processing-project"
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable billing (required for Cloud Run)
# Note: This requires manual setup in Google Cloud Console

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com 
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create Artifact Registry repository
gcloud artifacts repositories create audio-processing \
    --repository-format=docker \
    --location=$REGION \
    --description="Audio processing container images"

# Configure Docker for Artifact Registry
gcloud auth configure-docker $REGION-docker.pkg.dev

# Create Cloud Storage bucket
gsutil mb gs://$PROJECT_ID-audio-storage
```

### Step 2: Build Container Images

**Build CPU and GPU images:**

```bash
# Build CPU image
export IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/audio-processing/audio-processor"

docker build -t $IMAGE_URI:cpu .
docker push $IMAGE_URI:cpu

# Build GPU image with CUDA support
cat > Dockerfile.gpu << 'EOF'
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application
WORKDIR /app
COPY . .

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV WORKER_TYPE=gpu

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

docker build -f Dockerfile.gpu -t $IMAGE_URI:gpu .
docker push $IMAGE_URI:gpu
```

### Step 3: Deploy CPU Service

**Deploy main API service:**

```bash
# Deploy CPU service (main API)
gcloud run deploy audio-processor-api \
    --image=$IMAGE_URI:cpu \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --max-instances=100 \
    --min-instances=0 \
    --set-env-vars="WORKER_TYPE=cpu,STORAGE_TYPE=gcs,GCS_BUCKET=$PROJECT_ID-audio-storage,REDIS_URL=$UPSTASH_REDIS_URL" \
    --port=8080

# Get service URL
export API_URL=$(gcloud run services describe audio-processor-api --region=$REGION --format="value(status.url)")
echo "API URL: $API_URL"

# Test deployment
curl $API_URL/health
```

### Step 4: Deploy GPU Service

**Deploy GPU-enabled service for stem separation:**

```bash
# Deploy GPU service
gcloud run deploy audio-processor-gpu \
    --image=$IMAGE_URI:gpu \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=16Gi \
    --cpu=4 \
    --timeout=3600 \
    --max-instances=10 \
    --min-instances=0 \
    --gpu=1 \
    --gpu-type=nvidia-l4 \
    --set-env-vars="WORKER_TYPE=gpu,STORAGE_TYPE=gcs,GCS_BUCKET=$PROJECT_ID-audio-storage,REDIS_URL=$UPSTASH_REDIS_URL" \
    --port=8080

# Get GPU service URL
export GPU_URL=$(gcloud run services describe audio-processor-gpu --region=$REGION --format="value(status.url)")
echo "GPU Service URL: $GPU_URL"

# Test GPU deployment
curl $GPU_URL/health
```

---

## Phase 4: Feature Testing in Cloud

### Step 1: Test Audio Feature Extraction

**Test CPU-based feature extraction:**

```bash
# Upload test audio file to Cloud Storage
gsutil cp tests/fixtures/test_audio.wav gs://$PROJECT_ID-audio-storage/test/

# Test feature extraction API
curl -X POST $API_URL/storage/extract-features \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "test/test_audio.wav",
    "callback_url": "https://your-laravel-app.com/api/audio-processing/callback",
    "user_id": "test_user_001"
  }'

# Check Cloud Run logs
gcloud logs read --service=audio-processor-api --region=$REGION --limit=50
```

### Step 2: Test GPU Stem Separation

**Test GPU-accelerated stem separation:**

```bash
# Test stem separation with GPU
curl -X POST $GPU_URL/audio/separate-stems \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "test/test_audio.wav",
    "callback_url": "https://your-laravel-app.com/api/audio-processing/callback",
    "user_id": "test_user_001",
    "options": {
      "model": "mdx_extra",
      "output_format": "wav"
    }
  }'

# Monitor GPU service logs
gcloud logs read --service=audio-processor-gpu --region=$REGION --limit=50

# Check GPU utilization
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=audio-processor-gpu" --limit=10 --format=json
```

### Step 3: Test Tempo Processing

**Test tempo manipulation:**

```bash
# Test tempo processing
curl -X POST $API_URL/tempo/process-tempo \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "test/test_audio.wav",
    "effects_config": {
      "tempo_factor": 1.25,
      "pitch_shift": 3,
      "output_format": "wav"
    },
    "callback_url": "https://your-laravel-app.com/api/audio-processing/callback",
    "user_id": "test_user_001"
  }'
```

### Step 4: Test Error Handling

**Test error scenarios:**

```bash
# Test invalid audio file
curl -X POST $API_URL/storage/extract-features \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "test/nonexistent.wav",
    "callback_url": "https://your-laravel-app.com/api/audio-processing/callback",
    "user_id": "test_user_001"
  }'

# Test invalid parameters
curl -X POST $GPU_URL/audio/separate-stems \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "test/test_audio.wav",
    "callback_url": "invalid-url",
    "user_id": ""
  }'
```

---

## Phase 5: Laravel Integration Testing

### Step 1: Setup Laravel Webhook Handler

**Laravel callback endpoint:**

```php
// app/Http/Controllers/AudioProcessingController.php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use App\Models\AudioProcessingJob;

class AudioProcessingController extends Controller
{
    public function handleCallback(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'status' => 'required|string|in:completed,failed,processing',
            'user_id' => 'required|string',
            'job_id' => 'nullable|string',
            'analysis_summary' => 'nullable|array',
            'error' => 'nullable|string',
            'timestamp' => 'nullable|string'
        ]);

        $job = AudioProcessingJob::where('user_id', $validated['user_id'])
            ->where('status', 'processing')
            ->first();

        if (!$job) {
            return response()->json(['error' => 'Job not found'], 404);
        }

        $job->update([
            'status' => $validated['status'],
            'result_data' => $validated['analysis_summary'] ?? null,
            'error_message' => $validated['error'] ?? null,
            'completed_at' => now()
        ]);

        // Process completed job
        if ($validated['status'] === 'completed') {
            // Handle successful processing
            event(new AudioProcessingCompleted($job));
        } elseif ($validated['status'] === 'failed') {
            // Handle failed processing
            event(new AudioProcessingFailed($job));
        }

        return response()->json(['success' => true]);
    }
}
```

### Step 2: Test Laravel Integration

**Test callback integration:**

```bash
# Test callback with mock Laravel endpoint
export LARAVEL_CALLBACK_URL="https://your-laravel-app.com/api/audio-processing/callback"

# Submit job to Cloud Run
RESPONSE=$(curl -s -X POST $API_URL/storage/extract-features \
  -H "Content-Type: application/json" \
  -d "{
    \"storage_path\": \"test/test_audio.wav\",
    \"callback_url\": \"$LARAVEL_CALLBACK_URL\",
    \"user_id\": \"laravel_test_user\"
  }")

echo "Job submitted: $RESPONSE"

# Monitor callback in Laravel logs
# Laravel should receive callback within processing time
```

---

## Phase 6: Performance Optimization

### Step 1: Cold Start Optimization

**Optimize container startup:**

```dockerfile
# Optimized Dockerfile for faster cold starts
FROM python:3.11-slim

# Install runtime dependencies in single layer
RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Pre-install common packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-load ML models (optional)
RUN python -c "import librosa; import demucs.pretrained; demucs.pretrained.get_model('mdx_extra')"

WORKDIR /app
COPY . .

# Use exec form for faster startup
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

### Step 2: Configure Auto-Scaling

**Set optimal scaling parameters:**

```bash
# Update CPU service with optimized scaling
gcloud run services update audio-processor-api \
    --region=$REGION \
    --min-instances=1 \
    --max-instances=50 \
    --cpu-throttling \
    --concurrency=80

# Update GPU service with conservative scaling
gcloud run services update audio-processor-gpu \
    --region=$REGION \
    --min-instances=0 \
    --max-instances=5 \
    --concurrency=1 \
    --cpu-throttling
```

### Step 3: Monitor Performance

**Setup monitoring and alerting:**

```bash
# Create custom metrics
gcloud logging metrics create audio_processing_latency \
    --description="Audio processing latency" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.message="Processing completed"'

# Create alert policy for high latency
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring/latency-alert.yaml

# Monitor costs
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Audio Processing Budget" \
    --budget-amount=100USD \
    --threshold-rules-percent=80,90,100
```

---

## Phase 7: Cost Monitoring and Management

### Step 1: Cost Tracking Setup

**Monitor Cloud Run costs:**

```bash
# Get current month costs
gcloud billing budgets describe BUDGET_ID \
    --billing-account=BILLING_ACCOUNT_ID

# Export billing data to BigQuery for analysis
gcloud services enable bigquerydatatransfer.googleapis.com

# Setup cost alerts
gcloud alpha monitoring channels create \
    --channel-content-from-file=monitoring/cost-alerts.yaml
```

### Step 2: Usage Analysis

**Analyze usage patterns:**

```sql
-- BigQuery query for Cloud Run usage analysis
SELECT
  service.description as service_name,
  location.location as region,
  SUM(cost) as total_cost,
  SUM(usage.amount) as total_usage,
  AVG(cost / usage.amount) as avg_cost_per_unit
FROM `project-id.cloud_billing_export.gcp_billing_export_v1_BILLING_ACCOUNT_ID`
WHERE service.description LIKE '%Cloud Run%'
  AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY service_name, region
ORDER BY total_cost DESC
```

### Step 3: Cost Optimization Recommendations

**Based on usage analysis:**

1. **Scale GPU instances aggressively** - Keep min_instances=0 for GPU workloads
2. **Use CPU instances for burst capacity** - Scale up CPU instances before GPU
3. **Monitor request patterns** - Adjust concurrency limits based on actual usage
4. **Regional optimization** - Deploy closer to Laravel application to reduce latency and costs

---

## Conclusion and Next Steps

### Implementation Summary

✅ **Minimal Migration**: Existing FastAPI app containerized with minimal code changes  
✅ **GPU Support**: NVIDIA L4 GPUs deployed for stem separation workloads  
✅ **Cost Optimization**: True serverless scaling with 70-85% cost reduction  
✅ **Laravel Compatible**: Standard HTTP callbacks with no integration changes needed  
✅ **Production Ready**: Comprehensive testing, monitoring, and error handling  

### Expected Performance Metrics

- **Cold Start Time**: < 5 seconds for CPU, < 10 seconds for GPU
- **Processing Latency**: 2-15 seconds for feature extraction, 30-180 seconds for stem separation
- **Cost Reduction**: 70-85% versus traditional VPS hosting
- **Availability**: 99.9% uptime with automatic scaling

### Next Steps

1. **Production Deployment**: Deploy to production environment
2. **Load Testing**: Test with production-level traffic
3. **Cost Monitoring**: Monitor actual costs vs. projections
4. **Feature Enhancement**: Add new audio processing capabilities
5. **Multi-Region**: Deploy to multiple regions for global coverage

This implementation provides a robust, cost-effective serverless architecture that maintains compatibility with your existing Laravel application while dramatically reducing infrastructure costs and operational complexity.