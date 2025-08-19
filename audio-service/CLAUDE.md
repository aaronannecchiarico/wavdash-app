# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Initialize the project (installs dependencies, creates venv, configures .env)
python install.py

# Activate virtual environment
source beatforge-audio-extraction-service-local/bin/activate

# For fresh deployments: Run migration and seeding
python migrate_fresh.py  # Clears Redis, cache, initializes storage
python seed_data.py      # Seeds system with default data

# Start development environment (requires 2 terminals)
# Terminal 1: Start Celery worker
python start_worker.py

# Terminal 2: Start FastAPI server on 8001 for local
uvicorn main:app --reload --port 8001
```

### Testing
```bash
# Run all tests (unit + feature)
./run_tests.sh

# Run only unit tests (no external dependencies)
./run_tests.sh unit

# Run only feature tests (requires Redis + Celery worker)
./run_tests.sh feature

# Run specific test file
python -m pytest tests/unit/test_analysis_summary.py -v

# Run single test method
python -m pytest tests/unit/test_storage_structure.py::TestLocalStorageStructure::test_upload_analysis_result_with_user_id -v
```

### Migration and Maintenance
```bash
# Fresh deployment migration (clears all data)
python migrate_fresh.py

# Seed system with default data
python seed_data.py

# Validate setup and dependencies
python validate_setup.py

# Check configuration and device detection
python -c "from config import settings; print(f'Redis: {settings.REDIS_URL}')"
```

### Remote Migration API (Development Only)
For Laravel integration, migration endpoints are available via REST API when `DEBUG=true`:

```bash
# Check migration system status
curl -X GET http://localhost:8001/migration/status

# Run complete fresh migration (migration + seeding)
curl -X POST http://localhost:8001/migration/fresh

# Run migration only (without seeding)
curl -X POST http://localhost:8001/migration/migrate-only

# Run seeding only (without migration)
curl -X POST http://localhost:8001/migration/seed-only
```

**Security**: Migration endpoints are automatically blocked in production (`DEBUG=false`).
**Documentation**: See `MIGRATION_API_GUIDE.md` for complete Laravel integration guide.

## Architecture Overview

### Core Components

**FastAPI Application (`main.py`)**
- RESTful API with automatic OpenAPI documentation
- Modular router organization (health, audio, storage, tasks, tempo)
- Comprehensive request validation and error handling
- Clean separation of concerns with dedicated route modules

**Celery Task Queue (`celery_app.py`)**
- Distributed task processing with Redis broker
- Separate queues: `audio_features` and `stem_separation`
- Rate limiting and resource management
- Apple Silicon MPS compatibility handling

**Storage Abstraction (`services/storage_service.py`)**
- Local filesystem storage implementation
- User-based folder structure: `uploads/{user_id}/YYYY/MM/DD/` and `processed/{user_id}/YYYY/MM/DD/`
- Automatic directory creation and file management

### Task Processing Architecture

**Audio Processing Tasks (`tasks/audio_processing.py`)**
- Direct file upload processing (sync/async)
- Temporary file management and cleanup

**Storage Processing Tasks (`tasks/storage_processing.py`)**
- Process files already in storage (recommended for Laravel integration)
- Callback-based completion notifications
- Analysis summary generation for multi-chunk processing
- User-based path handling for local storage

**Feature Extraction (`services/audio_feature_extraction.py`)**
- Chunked processing for large files (>60s automatically split)
- Enhanced BPM detection with ensemble methods
- Musical analysis: key, tempo, loudness, brightness, duration
- Aggregated results for multi-chunk processing

### Data Models

**Request/Response Models (`models/`)**
- `audio_models.py`: Direct upload processing models
- `storage_models.py`: Storage-based processing models (Laravel integration)

**Route Organization (`routes/`)**
- `health.py`: Health checks and system status endpoints
- `audio_processing.py`: Direct file upload processing routes
- `storage.py`: Storage-based processing routes
- `tasks.py`: Task status and lifecycle management routes
- `tempo_processing.py`: Advanced tempo analysis features
- `migration.py`: Migration and maintenance endpoints (development only)

### Key Processing Flow

1. **Storage-based Processing** (Laravel Integration):
   - Laravel uploads file to shared storage
   - Calls `/storage/extract-features` with storage path
   - Microservice downloads, processes, uploads results
   - Sends callback with `analysis_summary` containing musical analysis
   - Laravel receives complete data without file reads

2. **Feature Extraction Logic**:
   - Short files (<60s): Single-chunk processing → `features` key
   - Long files (≥60s): Multi-chunk processing → `aggregated_features` key
   - Storage processing handles both structures for `analysis_summary`

## Critical Implementation Details

### Apple Silicon Compatibility
- Celery workers force CPU processing to prevent MPS multiprocessing crashes
- Automatic device detection and fallback in `utils/device_utils.py`
- Test environment handles both MPS and CPU scenarios

### Storage Path Structure
All processed files follow user-based organization:
```
uploads/{user_id}/2025/08/13/filename.mp3
processed/{user_id}/2025/08/13/filename_features.json
stems/{user_id}/2025/08/13/filename/vocals.wav
```

### Test Architecture
- **Unit Tests** (`tests/unit/`): Isolated component testing, no external dependencies
- **Feature Tests** (`tests/feature/`): Integration testing, requires Redis + Celery
- **Test Fixtures** (`tests/fixtures/`): BPM accuracy test audio with ground truth
- **Comprehensive mocking**: Storage tests mock environment variables and external dependencies

### Laravel Integration Patterns
- Callback-based async processing with `StorageCallbackData` model
- Musical analysis summary includes: BPM, key, key_confidence, loudness_db, brightness, duration
- User-based folder structure matches Laravel storage conventions
- Storage path configuration must align between Laravel and microservice
- **NEW**: Enhanced tempo processing with `TempoCallbackData` model
- **NEW**: Descriptive file naming for tempo processing (e.g., `song_tempo_nightcore-140-pitch+4.wav`)
- **NEW**: Complete tempo_processing metadata in callbacks with quality scores and warnings

## Environment Variables

**Required for Development:**
```bash
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage  # Must match Laravel path for local storage
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Performance Considerations

- Celery worker concurrency: 1 task per worker to prevent memory issues
- Rate limiting: 10/min for features, 5/min for stems, 3/min for batch
- Task time limits: 30min hard limit, 25min soft limit
- Automatic MPS fallback for CPU processing in worker processes

## Testing Patterns

When writing tests for storage functionality:
- Mock environment variables: `patch.dict('os.environ', {...})`
- Mock datetime for timestamp control: `patch('datetime.datetime')`
- Use `MagicMock` for external service dependencies (Redis)
- Test both user_id and no-user_id scenarios for storage paths