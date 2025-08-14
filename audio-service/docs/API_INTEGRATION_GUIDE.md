# Audio Processing Microservice - Laravel Integration Guide

## Service Overview

**Base URL**: `http://localhost:8000` (or your configured host/port)  
**Technology**: FastAPI + Celery + Redis  
**Shared Infrastructure**: Redis server on `localhost:6379`

## API Endpoints Summary

### 1. Health Check
```
GET /health
```
**Purpose**: Service status and connectivity check  
**Response**:
```json
{
    "status": "healthy",
    "redis_connected": {"worker1": "pong"},
    "version": "1.0.0",
    "device_info": {
        "platform": "darwin",
        "torch_version": "2.1.0",
        "device_type": "mps"
    }
}
```

### 2. Audio Feature Extraction (Async) - **RECOMMENDED**
```
POST /extract-features
Content-Type: multipart/form-data
```
**Parameters**:
- `audio_file`: File upload (WAV, MP3, FLAC, M4A, OGG)
- `async_processing`: boolean (default: true)
- `extract_detailed`: boolean (default: false)

**Response**:
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "processing",
    "message": "Audio processing started",
    "result": null
}
```

### 3. Task Summary (Laravel Optimized) - **RECOMMENDED FOR LARAVEL**
```
GET /task-summary/{task_id}
```
**Purpose**: Lightweight musical analysis perfect for database storage  
**Response**:
```json
{
    "task_id": "abc123-def456-ghi789",
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
    "chunk_count": 1,
    "key_changes": 1
}
```

### 4. Audio Feature Extraction (Sync) - **For Small Files**
```
POST /extract-features-sync
Content-Type: multipart/form-data
```
**Parameters**:
- `audio_file`: File upload
- `extract_detailed`: boolean (default: false)

**Use Case**: Files < 60 seconds, immediate response needed  
**Response**: Complete feature extraction results (similar to task-summary but synchronous)

### 5. Task Status (Detailed)
```
GET /task-status/{task_id}?include_result=false
```
**Parameters**:
- `include_result`: boolean (default: false)

**Response**:
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "completed",
    "message": "Processing completed successfully",
    "progress": 100,
    "result": null,  // or full results if include_result=true
    "error": null
}
```

### 6. Task Results (Full Data) - **WARNING: Large Response**
```
GET /task-result/{task_id}
```
**Purpose**: Complete feature extraction data including arrays  
**Use Case**: When you need MFCC coefficients, spectral data arrays, etc.

### 7. Task Management
```
DELETE /task/{task_id}
```
**Purpose**: Remove corrupted or stuck tasks from Redis

### 8. Stem Separation (Async)
```
POST /separate-stems
Content-Type: multipart/form-data
```
**Parameters**:
- `audio_file`: File upload
- `model_name`: string (default: "htdemucs")
- `async_processing`: boolean (default: true)

**Response**:
```json
{
    "task_id": "stem-task-id",
    "status": "processing",
    "message": "Stem separation started",
    "stems": null
}
```

**Available Models**: `htdemucs`, `htdemucs_ft`, `htdemucs_6s`, `mdx`, `mdx_extra`

### 9. Batch Processing
```
POST /batch-process
Content-Type: application/json
```
**Body**:
```json
{
    "filenames": ["song1.wav", "song2.wav"],
    "processing_type": "features",
    "model_name": "htdemucs"
}
```

## Task Status Flow

```
1. POST /extract-features → {task_id}
2. Polling: GET /task-status/{task_id} → status: "processing"
3. When complete: GET /task-summary/{task_id} → musical analysis
```

## Musical Analysis Data Structure

### Core Fields for Database Storage
```php
// Laravel Model fields suggestion
'key' => 'string',              // "E major", "A minor"
'key_confidence' => 'float',    // 0.0 - 1.0
'bpm' => 'integer',            // Rounded BPM value
'beat_regularity' => 'float',   // 0.0 - 1.0 rhythm consistency
'loudness_db' => 'float',       // Overall loudness in dB
'dynamic_range_db' => 'float',  // Compression level indicator
'brightness' => 'float',        // Spectral centroid (Hz)
'timbral_complexity' => 'float', // Texture complexity
'duration' => 'float',          // Track length in seconds
'processing_time' => 'float',   // Analysis duration
'chunk_count' => 'integer',     // Processing segments
'key_changes' => 'integer'      // Key modulations detected
```

### Value Ranges & Interpretation

**Key Detection**:
- Format: `"C major"`, `"F# minor"`, etc.
- Confidence > 0.8: Very reliable
- Confidence < 0.6: Atonal/complex

**BPM Classification**:
- 60-90: Slow (ballads)
- 90-120: Moderate (pop/rock)
- 120-140: Upbeat (dance)
- 140+: Fast (electronic/punk)

**Loudness (dB)**:
- -6 to 0: Very loud (compressed)
- -12 to -6: Loud (modern pop)
- -18 to -12: Moderate
- < -18: Quiet (acoustic)

**Dynamic Range (dB)**:
- > 20: High range (classical)
- 10-20: Moderate (rock)
- < 10: Compressed (pop/electronic)

**Brightness (Hz)**:
- < 1000: Dark/warm
- 1000-2000: Balanced
- > 2000: Bright

## Laravel Integration Examples

### 1. Basic Audio Upload & Processing
```php
use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;

class AudioProcessingService
{
    private string $baseUrl = 'http://localhost:8000';
    
    public function submitForProcessing(UploadedFile $audioFile): string
    {
        $response = Http::attach('audio_file', file_get_contents($audioFile), $audioFile->getClientOriginalName())
            ->post($this->baseUrl . '/extract-features');
            
        return $response->json('task_id');
    }
    
    public function getAnalysis(string $taskId): ?array
    {
        $response = Http::get($this->baseUrl . "/task-summary/{$taskId}");
        
        if ($response->json('status') === 'completed') {
            return $response->json('musical_analysis');
        }
        
        return null; // Still processing
    }
}
```

### 2. Database Model Integration
```php
// Migration
Schema::table('songs', function (Blueprint $table) {
    $table->string('analysis_task_id')->nullable();
    $table->string('musical_key')->nullable();
    $table->float('key_confidence')->nullable();
    $table->integer('bpm')->nullable();
    $table->float('beat_regularity')->nullable();
    $table->float('loudness_db')->nullable();
    $table->float('dynamic_range_db')->nullable();
    $table->float('brightness')->nullable();
    $table->float('timbral_complexity')->nullable();
    $table->integer('key_changes')->default(1);
    $table->float('analysis_duration')->nullable();
    $table->timestamp('analysis_completed_at')->nullable();
});

// Model method
public function updateMusicalAnalysis(array $analysis): void
{
    $this->update([
        'musical_key' => $analysis['key'],
        'key_confidence' => $analysis['key_confidence'],
        'bpm' => round($analysis['bpm']),
        'beat_regularity' => $analysis['beat_regularity'],
        'loudness_db' => $analysis['loudness_db'],
        'dynamic_range_db' => $analysis['dynamic_range_db'],
        'brightness' => $analysis['brightness'],
        'timbral_complexity' => $analysis['timbral_complexity'],
        'key_changes' => $analysis['key_changes'] ?? 1,
        'analysis_duration' => $analysis['processing_time'] ?? 0,
        'analysis_completed_at' => now(),
    ]);
}
```

### 3. Queue Job for Processing
```php
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;

class ProcessAudioAnalysisJob implements ShouldQueue
{
    use InteractsWithQueue, Queueable;
    
    public function __construct(
        private Song $song,
        private string $taskId
    ) {}
    
    public function handle(AudioProcessingService $service): void
    {
        $analysis = $service->getAnalysis($this->taskId);
        
        if ($analysis) {
            $this->song->updateMusicalAnalysis($analysis);
        } else {
            // Retry later if still processing
            $this->release(30); // Retry in 30 seconds
        }
    }
}
```

### 4. Music Recommendation Query
```php
public function findSimilarSongs(Song $song): Collection
{
    return Song::where('id', '!=', $song->id)
        ->where('musical_key', $song->musical_key)
        ->whereBetween('bpm', [$song->bpm - 10, $song->bpm + 10])
        ->whereBetween('brightness', [
            $song->brightness * 0.8, 
            $song->brightness * 1.2
        ])
        ->where('key_confidence', '>', 0.7)
        ->orderByRaw('ABS(bpm - ?)', [$song->bpm])
        ->limit(10)
        ->get();
}
```

## Redis Considerations

### Shared Redis Instance
- **Microservice uses**: Database 0 (default)
- **Key prefixes**: `celery-task-meta-*`, `audio_processing.*`
- **Laravel suggestion**: Use different database number or key prefixes
```php
// Laravel redis config
'redis' => [
    'default' => [
        'host' => 'localhost',
        'port' => 6379,
        'database' => 1, // Different from microservice
    ]
]
```

### Task Cleanup
- Tasks auto-expire after 24 hours
- Use `DELETE /task/{task_id}` for manual cleanup
- Monitor Redis memory usage

## Error Handling

### Common HTTP Status Codes
- `200`: Success
- `422`: Validation error (invalid file format)
- `413`: File too large
- `500`: Processing error

### Task Status Values
- `"pending"`: Queued for processing
- `"processing"`: Currently being analyzed
- `"completed"`: Analysis finished successfully
- `"failed"`: Error occurred during processing

### Error Response Format
```json
{
    "detail": "File format not supported",
    "error": {
        "type": "UnsupportedFormatError",
        "message": "Unsupported format: txt"
    }
}
```

## Performance Notes

### File Size Limits
- Default: 100MB per file
- Configurable via `MAX_FILE_SIZE` environment variable

### Processing Times
- Small files (< 60s): 1-3 seconds
- Medium files (3-5 min): 5-15 seconds  
- Large files (> 10 min): 30-120 seconds

### Concurrent Processing
- Default: 4 concurrent Celery workers
- Each worker can handle 1 audio file at a time
- Queue supports unlimited pending tasks

### Recommended Laravel Flow
1. Upload file → Submit to microservice → Store `task_id`
2. Background job polls for completion
3. Store analysis results in Laravel database
4. Use Laravel data for queries/recommendations
5. Optionally cache common analysis patterns

## Development/Testing

### Curl Examples
```bash
# Submit audio file
curl -X POST "http://localhost:8000/extract-features" \
  -F "audio_file=@song.mp3"

# Get lightweight analysis (recommended)
curl "http://localhost:8000/task-summary/YOUR_TASK_ID"

# Health check
curl "http://localhost:8000/health"
```

### Environment Variables
```bash
# Microservice .env
HOST=0.0.0.0
PORT=8000
REDIS_HOST=localhost
REDIS_PORT=6379
DEBUG=false
MAX_FILE_SIZE=104857600
```

This microservice is production-ready with comprehensive error handling, automatic device detection (MPS/CUDA/CPU), and optimized for Laravel integration through the `/task-summary` endpoint.