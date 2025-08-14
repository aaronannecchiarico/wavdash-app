# Audio Processing Microservice

A FastAPI-based microservice for audio feature extraction and AI-powered stem separation using Celery for distributed task processing.

## Features

- **Audio Feature Extraction**: Extract comprehensive audio features using Librosa
  - MFCC, Chroma, Spectral features
  - Tempo, rhythm, and harmony analysis
  - Pitch and onset detection
  
- **AI Stem Separation**: Separate audio into stems using Demucs
  - Vocals, drums, bass, and other instruments
  - Multiple pre-trained models available
  
- **Asynchronous Processing**: Celery-based task queue with Redis
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Containerized**: Docker and Docker Compose support
- **GPU Support**: Optional CUDA acceleration for AI models

## Installation

### Quick Installation (Recommended)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the installation script
python install.py
```

The installer will:
- ✅ Detect your platform (Apple Silicon MPS, CUDA, or CPU)
- ✅ Install all required packages (FastAPI, Celery, PyTorch, Librosa, Demucs)
- ✅ Test all imports and functionality
- ✅ Create a configured .env file
- ✅ Provide next steps for running the service

### Manual Installation

```bash
# Install from requirements file
pip install -r requirements.txt
```

### Docker

```bash
# CPU-only
docker-compose up

# GPU-enabled
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up
```

## Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings:
   ```bash
   # Server Configuration
   HOST=0.0.0.0
   PORT=8000
   DEBUG=False
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   
   # GPU Configuration (if available)
   DEMUCS_DEVICE=cuda  # or cpu
   ```

## Quick Start

After installation, start the services:

### Local Development

```bash
# Terminal 1: Start Celery worker
python start_worker.py

# Terminal 2: Start FastAPI server  
uvicorn main:app --reload
```

### Using Docker

```bash
# Start all services (Redis, API, Worker, Monitoring)
docker-compose up -d

# Check status
docker-compose ps
```

### Services

Once running, you can access:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs  
- **Health Check**: http://localhost:8000/health
- **Flower Monitoring**: http://localhost:5555 (Docker only)

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status, Redis connectivity, device information, and storage configuration.

### Storage Configuration
```
GET /storage/status
```
Check current storage configuration (local or R2) and availability.

### File-Based Audio Processing (Direct Upload)

#### Audio Feature Extraction (Async)
```
POST /extract-features
Content-Type: multipart/form-data

Parameters:
- audio_file: Audio file (WAV, MP3, FLAC, M4A, OGG)
- async_processing: Boolean (default: true)
```
Upload and process audio file directly. Returns task ID for tracking.

#### Audio Feature Extraction (Sync)
```
POST /extract-features-sync
Content-Type: multipart/form-data

Parameters:
- audio_file: Audio file
- extract_detailed: Boolean (default: false)
```
Immediate processing for small files (< 60 seconds recommended).

#### Stem Separation (Async)
```
POST /separate-stems
Content-Type: multipart/form-data

Parameters:
- audio_file: Audio file
- model_name: Demucs model (default: "htdemucs")
- async_processing: Boolean (default: true)
```
Upload and separate audio into stems (vocals, drums, bass, other).

### Storage-Based Audio Processing (Recommended)

**For Laravel integration with existing file storage:**

#### Storage Feature Extraction
```
POST /storage/extract-features
Content-Type: application/json

{
  "storage_path": "uploads/user_id/2025/08/13/filename.mp3",
  "extract_detailed": false,
  "callback_url": "https://your-app.com/api/audio/analysis/callback/123",
  "metadata": {
    "user_id": "1",
    "upload_id": "123",
    "original_filename": "song.mp3"
  }
}
```
Process audio files already in storage. **Recommended for production.**

#### Storage Stem Separation
```
POST /storage/separate-stems
Content-Type: application/json

{
  "storage_path": "uploads/user_id/2025/08/13/filename.mp3",
  "model_name": "htdemucs",
  "callback_url": "https://your-app.com/api/audio/analysis/callback/123",
  "metadata": {
    "user_id": "1",
    "upload_id": "123"
  }
}
```

#### Storage File Operations
```
GET /storage/file-info/{path}     # Get file information
GET /storage/list-files?prefix=   # List files with optional prefix
DELETE /storage/file/{path}       # Delete file from storage
```

#### Batch Processing
```
POST /storage/batch-process
Content-Type: application/json

{
  "storage_paths": ["uploads/1/file1.mp3", "uploads/1/file2.mp3"],
  "processing_type": "features",  // or "stems"
  "callback_url": "https://your-app.com/api/batch-callback",
  "batch_metadata": {"batch_id": "batch_123"}
}
```

### Task Management

#### Task Status (Detailed)
```
GET /task-status/{task_id}?include_result=false
```
Returns task status with optional full results. Default is summary only.

#### Task Summary (Laravel-Optimized)
```
GET /task-summary/{task_id}
```
**Recommended for Laravel integration.** Returns lightweight musical analysis data without large arrays.

#### Task Results (Full Data)
```
GET /task-result/{task_id}
```
Returns complete feature extraction data. **Warning: May be very large.**

#### Task Deletion
```
DELETE /task/{task_id}
```
Remove corrupted or stuck tasks from Redis backend. **Task status will show as "deleted" after removal.**

### Important Notes

- **Storage paths**: All processed files respect user-based folder structure: `processed/user_id/2025/08/13/filename_features.json`
- **Apple Silicon compatibility**: Stem separation automatically uses CPU processing to prevent MPS multiprocessing crashes
- **Audio format handling**: Mono audio is automatically converted to stereo for Demucs models
- **Task tracking**: Deleted tasks properly return "deleted" status instead of "pending"

## Example Usage

### Storage-Based Processing (Recommended)

```python
import requests

# Process file already in storage
response = requests.post(
    'http://localhost:8000/storage/extract-features',
    json={
        "storage_path": "uploads/1/2025/08/13/audio-uuid.mp3",
        "extract_detailed": False,
        "callback_url": "https://yourapp.com/api/callback/123",
        "metadata": {
            "user_id": "1",
            "upload_id": "123",
            "original_filename": "song.mp3"
        }
    }
)

task_id = response.json()['task_id']

# Check task status
status_response = requests.get(f'http://localhost:8000/task-summary/{task_id}')
analysis = status_response.json()

print(f"Key: {analysis['musical_analysis']['key']}")
print(f"BPM: {analysis['musical_analysis']['bpm']}")
print(f"Processed file: {analysis['storage_analysis_path']}")
```

### Direct File Upload

```python
import requests

# Upload audio for feature extraction
with open('audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/extract-features',
        files={'audio_file': f}
    )

task_id = response.json()['task_id']

# Check task status
status_response = requests.get(f'http://localhost:8000/task-status/{task_id}')
print(status_response.json())
```

### cURL Examples

```bash
# Storage-based processing (recommended)
curl -X POST "http://localhost:8000/storage/extract-features" \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "uploads/1/2025/08/13/audio.mp3",
    "callback_url": "https://yourapp.com/callback/123",
    "metadata": {"user_id": "1", "upload_id": "123"}
  }'

# Direct file upload
curl -X POST "http://localhost:8000/extract-features" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@audio.wav"

# Get lightweight summary (perfect for Laravel)
curl "http://localhost:8000/task-summary/YOUR_TASK_ID"

# Check storage status
curl "http://localhost:8000/storage/status"
```

## Musical Analysis Results

The `/task-summary/{task_id}` endpoint returns lightweight, Laravel-friendly musical analysis data:

### Example Response

```json
{
  "task_id": "abc123-def456",
  "status": "completed",
  "metadata": {
    "filename": "song.mp3",
    "duration": 180.5,
    "sample_rate": 22050,
    "processing_time": 3.2
  },
  "musical_analysis": {
    "key": "E major",
    "key_confidence": 0.85,
    "bpm": 114.5,
    "beat_regularity": 0.78,
    "loudness_db": -12.3,
    "dynamic_range_db": 18.2,
    "brightness": 1850.2,
    "timbral_complexity": 0.45
  },
  "chunk_count": 5
}
```

### Understanding the Analysis

#### **Musical Key Detection**
- **`key`**: Detected musical key using Krumhansl-Schmuckler algorithm
  - Format: `"C major"`, `"A minor"`, `"F# major"`, etc.
  - Useful for: Key matching, harmonic analysis, music recommendation
  
- **`key_confidence`**: Confidence score (0.0 - 1.0)
  - `> 0.8`: Very confident detection
  - `0.6 - 0.8`: Good detection
  - `< 0.6`: Uncertain, may be atonal or complex harmony

#### **Tempo & Rhythm Analysis**
- **`bpm`**: Beats per minute (tempo)
  - `60-90`: Slow (ballads, ambient)
  - `90-120`: Moderate (pop, rock)
  - `120-140`: Upbeat (dance, pop)
  - `140+`: Fast (electronic, punk)

- **`beat_regularity`**: Rhythmic consistency (0.0 - 1.0)
  - `> 0.8`: Very steady rhythm (electronic, metronome-like)
  - `0.5 - 0.8`: Moderate consistency (live music)
  - `< 0.5`: Irregular rhythm (jazz, experimental)

- **`bpm_stability`**: Tempo variation across the song
  - Lower values = more consistent tempo
  - Higher values = tempo changes throughout

#### **Audio Dynamics**
- **`loudness_db`**: Overall loudness in decibels
  - `-6 to 0 dB`: Very loud (heavily compressed)
  - `-12 to -6 dB`: Loud (modern pop)
  - `-18 to -12 dB`: Moderate (balanced mix)
  - `< -18 dB`: Quiet (classical, acoustic)

- **`dynamic_range_db`**: Difference between loudest and quietest parts
  - `> 20 dB`: High dynamic range (classical, jazz)
  - `10-20 dB`: Moderate range (rock, indie)
  - `< 10 dB`: Compressed (pop, electronic)

#### **Tonal Characteristics**
- **`brightness`**: Spectral centroid in Hz - perceived "brightness"
  - `< 1000 Hz`: Dark, warm (bass-heavy, mellow)
  - `1000-2000 Hz`: Balanced (vocals, mid-range instruments)
  - `> 2000 Hz`: Bright (cymbals, high-pitched instruments)

- **`timbral_complexity`**: Variation in timbre/texture
  - `> 0.5`: Complex (orchestral, dense arrangements)
  - `0.2-0.5`: Moderate (band arrangements)
  - `< 0.2`: Simple (single instrument, minimal)

#### **Processing Information**
- **`chunk_count`**: Number of segments analyzed (for long tracks)
  - `1`: Processed as single file (< 60 seconds)
  - `2+`: Processed in chunks, results are aggregated

- **`key_changes`**: Number of different keys detected across chunks
  - `1`: Consistent key throughout
  - `2+`: Key changes or modulations detected

### Laravel Integration Example

```php
// Process the musical analysis data
$analysis = $response['musical_analysis'];

// Classify the song
$energy_level = $analysis['bpm'] > 120 ? 'high' : 'low';
$mood = strpos($analysis['key'], 'major') !== false ? 'happy' : 'melancholy';
$production_style = $analysis['dynamic_range_db'] > 15 ? 'natural' : 'compressed';

// Store in database
Song::create([
    'filename' => $response['metadata']['filename'],
    'key' => $analysis['key'],
    'bpm' => round($analysis['bpm']),
    'energy_level' => $energy_level,
    'mood' => $mood,
    'loudness' => $analysis['loudness_db'],
    'brightness' => $analysis['brightness'],
    'production_style' => $production_style
]);

// Use for recommendations
$similar_songs = Song::where('key', $analysis['key'])
                    ->whereBetween('bpm', [$analysis['bpm'] - 10, $analysis['bpm'] + 10])
                    ->where('energy_level', $energy_level)
                    ->get();
```

## Available Demucs Models

- `htdemucs`: Hybrid transformer model (recommended)
- `htdemucs_ft`: Fine-tuned version
- `htdemucs_6s`: 6-stem separation
- `mdx`: MDX model
- `mdx_extra`: MDX with extra training data

## Development

### Testing

The project includes comprehensive unit and feature tests organized in a clear structure:

```
tests/
├── unit/           # Unit tests for individual components
├── feature/        # End-to-end feature tests
└── fixtures/       # Test data and utilities
```

#### Running Tests

**Recommended: Use the test runner script**
```bash
# Run all tests
./run_tests.sh

# Run only unit tests
./run_tests.sh unit

# Run only feature tests  
./run_tests.sh feature
```

**Manual pytest execution (ensure you're in the venv)**
```bash
# Activate virtual environment
source beatforge-audio-extraction-service-local/bin/activate

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/feature/       # Feature tests only
pytest -m "not slow"        # Skip slow tests
```

#### Test Categories

- **Unit Tests**: Test individual components in isolation
  - `test_audio_utils.py` - Audio processing utilities
  - `test_device_utils.py` - Device detection and GPU handling  
  - `test_audio_models.py` - Pydantic data models
  - `test_config.py` - Configuration management

- **Feature Tests**: Test complete workflows
  - `test_setup.py` - Environment and dependency verification
  - `test_feature_service.py` - Audio feature extraction service
  - `test_celery_integration.py` - Celery task processing
  - `test_stem_separation.py` - AI stem separation functionality

#### Test Requirements

**Unit Tests**: No external dependencies required

**Feature Tests**: Require running services
- Redis server
- Celery worker (for integration tests)

#### Setting Up Test Environment

```bash
# 1. Install and activate environment
python install.py
source beatforge-audio-extraction-service-local/bin/activate

# 2. Start Redis (if running feature tests)
docker run -d -p 6379:6379 redis:alpine

# 3. Start Celery worker (for integration tests)
python start_worker.py

# 4. Run tests
./run_tests.sh
```

### Code Formatting

```bash
# Activate virtual environment first
source beatforge-audio-extraction-service-local/bin/activate

# Format code
black .
isort .
flake8 .
```

### Starting Development Server

```bash
# Activate virtual environment first
source beatforge-audio-extraction-service-local/bin/activate

# Start development server
uvicorn main:app --reload --log-level debug --port 8001
```

## Production Deployment

### Docker with GPU Support

Create `docker-compose.gpu.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      args:
        ENABLE_GPU: "true"
    runtime: nvidia
    environment:
      - DEMUCS_DEVICE=cuda

  worker:
    build:
      context: .
      args:
        ENABLE_GPU: "true"
    runtime: nvidia
    environment:
      - DEMUCS_DEVICE=cuda
```

Deploy:
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `False` | Debug mode |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `DEMUCS_DEVICE` | `cpu` | Device for AI models |
| `MAX_FILE_SIZE` | `104857600` | Max upload size (bytes) |
| `TASK_TIME_LIMIT` | `1800` | Task timeout (seconds) |
| **Storage Configuration** | | |
| `STORAGE_TYPE` | `local` | Storage type (`local` or `r2`) |
| `LOCAL_STORAGE_PATH` | `./storage` | Local storage base path |
| `LOCAL_STORAGE_PUBLIC_URL` | | Public URL for local files |
| **R2 Cloud Storage** | | |
| `R2_ACCESS_KEY_ID` | | R2 access key |
| `R2_SECRET_ACCESS_KEY` | | R2 secret key |
| `R2_BUCKET` | | R2 bucket name |
| `R2_ENDPOINT` | | R2 endpoint URL |
| `R2_PUBLIC_URL` | | R2 public URL |

## Monitoring

### Flower (Celery Monitoring)

Access Flower at http://localhost:5555 to monitor:
- Active workers
- Task statistics
- Queue status
- Task history

### Logs

Logs are stored in the `logs/` directory:
- `app.log`: Application logs
- `celery.log`: Celery worker logs  
- `error.log`: Error logs only

## Known Warnings & Their Resolution

During testing and development, you may encounter several types of warnings. Most have been resolved or are documented below:

### Resolved Warnings

✅ **FFT Size Warnings** - Fixed in v1.0
- **Issue**: `UserWarning: n_fft=1024 is too large for input signal of length 256`
- **Resolution**: Dynamic n_fft calculation based on audio length
- **Technical**: The service now automatically adjusts FFT window size to prevent warnings while maintaining audio analysis quality

### Unavoidable External Library Warnings

⚠️ **Python 3.13 Deprecated Module Warnings** - External Package Issue
```
DeprecationWarning: aifc was removed in Python 3.13. Please be aware that you are currently NOT using standard 'aifc', but instead a separately installed 'standard-aifc'.
DeprecationWarning: sunau was removed in Python 3.13. Please be aware that you are currently NOT using standard 'sunau', but instead a separately installed 'standard-sunau'.
```
- **Source**: `audioread` package (dependency of librosa)
- **Impact**: None - functionality works correctly
- **Resolution**: Package maintainers will update for Python 3.13 compatibility
- **Action**: Safe to ignore - no impact on audio processing

⚠️ **Librosa Deprecation Warning** - External Package Issue
```
FutureWarning: librosa.core.audio.__audioread_load
```
- **Source**: librosa internal implementation
- **Impact**: None - functionality works correctly
- **Resolution**: Will be fixed in future librosa releases
- **Action**: Safe to ignore - no impact on audio processing

⚠️ **PySoundFile Fallback Warning** - Test Environment Only
```
UserWarning: PySoundFile failed. Trying audioread instead.
```
- **Source**: Invalid test audio data in unit tests
- **Impact**: None - tests pass correctly
- **Context**: Only occurs with synthetic test audio in unit tests
- **Action**: Safe to ignore - real audio files process without warnings

### Warning Summary

- **Total warnings reduced**: From ~20+ to 4-6 warnings
- **User-impacting warnings**: 0 (all resolved)
- **Remaining warnings**: External library compatibility issues only
- **Production impact**: None - all functionality works correctly

The service prioritizes functionality and reliability. All remaining warnings are from external dependencies and do not affect audio processing quality or reliability.

## Troubleshooting

### Common Issues

1. **GPU not detected**:
   - Verify CUDA installation: `nvidia-smi`
   - Check PyTorch CUDA support: `python -c "import torch; print(torch.cuda.is_available())"`

2. **Redis connection errors**:
   - Ensure Redis is running: `docker run -d -p 6379:6379 redis:alpine`
   - Check Redis connectivity: `redis-cli ping`

3. **Out of memory errors**:
   - Reduce batch size or use CPU mode
   - Set `DEMUCS_DEVICE=cpu` in environment

4. **Unsupported audio format**:
   - Convert to supported format: WAV, MP3, FLAC, M4A, OGG
   - Install additional codecs: `apt-get install ffmpeg`

5. **Celery worker crashes with SIGABRT (Apple Silicon)**:
   - This is fixed automatically - Celery workers use CPU for stem separation
   - MPS (Metal Performance Shaders) causes multiprocessing crashes
   - The service automatically detects and handles this issue

6. **Demucs model expects stereo input error**:
   - Fixed automatically - mono audio is converted to stereo
   - All audio is properly formatted for Demucs requirements
   - Error: "expected input to have 2 channels, but got 1 channels instead"

### Performance Optimization

- Use GPU acceleration for faster processing
- Adjust Celery concurrency based on available resources
- Use SSD storage for temporary files
- Monitor memory usage with Flower

## License

This project is licensed under the MIT License.