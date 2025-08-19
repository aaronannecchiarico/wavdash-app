# Laravel Integration Guide

This document provides comprehensive guidance for integrating your Laravel application with the Beat Forge Audio Feature Extraction Microservice.

## Overview

The microservice provides unified audio processing capabilities with configurable storage (local or Cloudflare R2) via REST API endpoints. Your Laravel app uploads files to shared storage, then calls the microservice for processing.

## Architecture

```
[Laravel App] --> [Shared Storage] <-- [Audio Microservice]
                      |
                  (Local/R2)
```

## Configuration

### Storage Types

The microservice supports two storage backends:
- **Local Storage**: Files stored on local filesystem
- **Cloudflare R2**: Cloud object storage (S3-compatible)

### Environment Variables

#### Microservice Configuration
```bash
# Storage Configuration
STORAGE_TYPE=local  # or 'r2'

# Local Storage (when STORAGE_TYPE=local)
# IMPORTANT: Must match Laravel's private storage path
LOCAL_STORAGE_PATH=/path/to/your/laravel/storage/app/private
LOCAL_STORAGE_PUBLIC_URL=

# Cloudflare R2 (when STORAGE_TYPE=r2)
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET=forge-audio
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://forge-audio.your-account-id.r2.dev
```

#### Laravel Configuration
Your Laravel app should use the same storage location. Since both services access the same filesystem:

**For Local Storage:**
- Laravel uses: `storage_path('app/private')` → `/your/laravel/storage/app/private`  
- Microservice uses: `LOCAL_STORAGE_PATH=/your/laravel/storage/app/private`
- **File Structure**: All files follow user-based structure: `uploads/{user_id}/2025/08/13/filename.mp3`
- **Processed Files**: Stored as `processed/{user_id}/2025/08/13/filename_features.json`

**For R2 Storage:**
- Both services use the same R2 bucket configuration
- Laravel uses the 'r2' disk configuration  
- Microservice uses the R2_* environment variables
- **Same folder structure**: Files organized by user_id for both uploads and processed results

## API Endpoints

### Health Check
```http
GET /
GET /health
```
Check service status and health.

### Storage Operations

#### Storage Status
```http
GET /storage/status
```
Check storage configuration and availability.

#### Feature Extraction (Async)
```http
POST /storage/extract-features
Content-Type: application/json

{
    "storage_path": "uploads/123/2025/08/13/song.wav",
    "extract_detailed": false,
    "callback_url": "https://your-laravel-app.com/api/audio/analysis/callback/123",
    "metadata": {
        "user_id": "123",
        "upload_id": "456",
        "original_filename": "song.wav"
    }
}
```

#### Stem Separation (Async)
```http
POST /storage/separate-stems
Content-Type: application/json

{
    "storage_path": "uploads/123/2025/08/13/song.wav",
    "model_name": "htdemucs",
    "callback_url": "https://your-laravel-app.com/api/audio/stems/callback/123",
    "metadata": {
        "user_id": "123",
        "upload_id": "456",
        "original_filename": "song.wav"
    }
}
```

#### File Information
```http
GET /storage/file-info/{storage_path}
```

#### List Files
```http
GET /storage/list-files?prefix=uploads/&max_keys=100
```

#### Delete File
```http
DELETE /storage/file/{storage_path}
```

#### Batch Processing
```http
POST /storage/batch-process
Content-Type: application/json

{
    "storage_paths": [
        "uploads/123/2025/01/01/song1.wav",
        "uploads/123/2025/01/01/song2.wav"
    ],
    "processing_type": "features",
    "callback_url": "https://your-laravel-app.com/api/batch/processed/123",
    "batch_metadata": {
        "batch_id": "batch_123",
        "user_id": "456"
    }
}
```

### Task Management

#### Task Status (Full Details)
```http
GET /task/status/{task_id}?include_result=false
```
Get task status with optional full result data.

#### Task Result (Full Data)
```http
GET /task/result/{task_id}
```
Get complete task result data (may be large).

#### Task Summary (Laravel Optimized)
```http
GET /task/summary/{task_id}
```
Get lightweight summary for Laravel integration - only essential metrics.

#### Delete Task
```http
DELETE /task/{task_id}
```
Delete corrupted or stuck task.

### Direct Audio Processing

#### Feature Extraction (Direct Upload)
```http
POST /audio/extract-features
Content-Type: multipart/form-data

file: [audio file]
extract_detailed: false
```

#### Stem Separation (Direct Upload)
```http
POST /audio/separate-stems
Content-Type: multipart/form-data

file: [audio file]
model_name: htdemucs
```

#### Sync Feature Extraction
```http
POST /audio/extract-features-sync
Content-Type: multipart/form-data

file: [audio file]
```

### Tempo Processing

#### Tempo Processing (Direct Upload)
```http
POST /tempo/process
Content-Type: multipart/form-data

file: [audio file]
preset: "nightcore"
tempo_factor: 1.4
pitch_shift_semitones: 4.0
preserve_pitch: false
add_reverb: false
use_stems: true
```

#### Sync Tempo Processing
```http
POST /tempo/process-sync
Content-Type: multipart/form-data

file: [audio file]
preset: "slowed_reverb"
tempo_factor: 0.75
pitch_shift_semitones: -2.0
```

#### Tempo Processing (Storage)
```http
POST /tempo/storage/process
Content-Type: application/json

{
    "storage_path": "uploads/123/2025/08/13/song.wav",
    "preset": "nightcore",
    "tempo_factor": 1.4,
    "pitch_shift_semitones": 4.0,
    "preserve_pitch": false,
    "add_reverb": false,
    "use_stems": true,
    "callback_url": "https://your-app.com/api/tempo/callback/123",
    "metadata": {
        "user_id": "123",
        "original_filename": "song.wav"
    }
}
```

#### Get Available Presets
```http
GET /tempo/presets
```

#### System Compatibility Check
```http
GET /tempo/system/compatibility
```

#### Suggest Presets
```http
GET /tempo/suggest-presets?current_bpm=120&target_bpm=128
```

#### Performance Metrics
```http
GET /tempo/performance/metrics
```

#### Clear Performance Cache
```http
POST /tempo/performance/cache/clear
```

## Laravel Implementation Example

### 1. File Upload Service

```php
<?php

namespace App\Services;

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class AudioStorageService
{
    protected string $storageDisk;
    protected string $microserviceUrl;
    
    public function __construct()
    {
        // Use 'local' for local filesystem, 'r2' for Cloudflare R2
        $this->storageDisk = config('audio.storage_disk', 'local');
        $this->microserviceUrl = config('audio.microservice_url');
    }
    
    public function uploadFile(UploadedFile $file, int $userId, array $metadata = []): array
    {
        // Generate UUID for unique filename
        $uuid = Str::uuid();
        $extension = $file->getClientOriginalExtension();
        
        // Generate path matching microservice structure: uploads/{user_id}/2025/08/13/{uuid}.{ext}
        $date = now()->format('Y/m/d');
        $filename = "{$uuid}.{$extension}";
        $storagePath = "uploads/{$userId}/{$date}/{$filename}";
        
        // Store file in shared storage location (private disk)
        // Laravel will store to storage/app/private/{storagePath}
        // Microservice will access from LOCAL_STORAGE_PATH/{storagePath}
        $path = Storage::disk($this->storageDisk)->putFileAs(
            dirname($storagePath),
            $file,
            basename($storagePath)
        );
        
        return [
            'storage_path' => $storagePath,
            'uuid' => $uuid,
            'local_path' => Storage::disk($this->storageDisk)->path($storagePath),
            'size' => $file->getSize(),
            'original_name' => $file->getClientOriginalName(),
            'metadata' => $metadata
        ];
    }
    
    public function deleteFile(string $storagePath): bool
    {
        return Storage::disk($this->storageDisk)->delete($storagePath);
    }
}
```

### 2. Microservice Client

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AudioMicroserviceClient
{
    protected string $baseUrl;
    
    public function __construct()
    {
        $this->baseUrl = rtrim(config('audio.microservice_url'), '/');
    }
    
    public function extractFeatures(string $storagePath, array $options = []): array
    {
        $response = Http::timeout(30)->post("{$this->baseUrl}/storage/extract-features", [
            'storage_path' => $storagePath,
            'extract_detailed' => $options['detailed'] ?? false,
            'callback_url' => $options['callback_url'] ?? null,
            'metadata' => $options['metadata'] ?? []
        ]);
        
        if ($response->failed()) {
            throw new \Exception("Microservice error: " . $response->body());
        }
        
        return $response->json();
    }
    
    public function separateStems(string $storagePath, array $options = []): array
    {
        $response = Http::timeout(30)->post("{$this->baseUrl}/storage/separate-stems", [
            'storage_path' => $storagePath,
            'model_name' => $options['model'] ?? 'htdemucs',
            'callback_url' => $options['callback_url'] ?? null,
            'metadata' => $options['metadata'] ?? []
        ]);
        
        if ($response->failed()) {
            throw new \Exception("Microservice error: " . $response->body());
        }
        
        return $response->json();
    }
    
    public function getTaskSummary(string $taskId): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/task/summary/{$taskId}");
        
        if ($response->failed()) {
            throw new \Exception("Failed to get task summary: " . $response->body());
        }
        
        return $response->json();
    }
    
    public function getTaskStatus(string $taskId, bool $includeResult = false): array
    {
        $url = "{$this->baseUrl}/task/status/{$taskId}";
        if ($includeResult) {
            $url .= "?include_result=true";
        }
        
        $response = Http::timeout(10)->get($url);
        
        if ($response->failed()) {
            throw new \Exception("Failed to get task status: " . $response->body());
        }
        
        return $response->json();
    }
    
    public function deleteTask(string $taskId): array
    {
        $response = Http::timeout(10)->delete("{$this->baseUrl}/task/{$taskId}");
        
        if ($response->failed()) {
            throw new \Exception("Failed to delete task: " . $response->body());
        }
        
        return $response->json();
    }
    
    public function batchProcess(array $storagePaths, string $processingType, array $options = []): array
    {
        $response = Http::timeout(30)->post("{$this->baseUrl}/storage/batch-process", [
            'storage_paths' => $storagePaths,
            'processing_type' => $processingType,
            'model_name' => $options['model'] ?? 'htdemucs',
            'callback_url' => $options['callback_url'] ?? null,
            'batch_metadata' => $options['batch_metadata'] ?? []
        ]);
        
        if ($response->failed()) {
            throw new \Exception("Batch processing failed: " . $response->body());
        }
        
        return $response->json();
    }
    
    public function getStorageStatus(): array
    {
        $response = Http::timeout(5)->get("{$this->baseUrl}/storage/status");
        
        if ($response->failed()) {
            throw new \Exception("Storage status check failed: " . $response->body());
        }
        
        return $response->json();
    }
}
```

### 3. Audio Processing Job

```php
<?php

namespace App\Jobs;

use App\Models\AudioFile;
use App\Services\AudioMicroserviceClient;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class ProcessAudioFileJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;
    
    public function __construct(
        public AudioFile $audioFile,
        public string $processingType = 'features',
        public array $options = []
    ) {}
    
    public function handle(AudioMicroserviceClient $client)
    {
        try {
            $callbackUrl = route('api.audio.processed', $this->audioFile);
            
            $result = match($this->processingType) {
                'features' => $client->extractFeatures($this->audioFile->storage_path, [
                    'detailed' => $this->options['detailed'] ?? false,
                    'callback_url' => $callbackUrl,
                    'metadata' => [
                        'user_id' => $this->audioFile->user_id,
                        'upload_id' => $this->audioFile->id,
                        'original_filename' => $this->audioFile->original_filename
                    ]
                ]),
                'stems' => $client->separateStems($this->audioFile->storage_path, [
                    'model' => $this->options['model'] ?? 'htdemucs',
                    'callback_url' => $callbackUrl,
                    'metadata' => [
                        'user_id' => $this->audioFile->user_id,
                        'upload_id' => $this->audioFile->id,
                        'original_filename' => $this->audioFile->original_filename
                    ]
                ])
            };
            
            // Update audio file with task information
            $this->audioFile->update([
                'microservice_task_id' => $result['task_id'],
                'processing_status' => 'processing',
                'processing_type' => $this->processingType
            ]);
            
            Log::info("Audio processing started", [
                'audio_file_id' => $this->audioFile->id,
                'task_id' => $result['task_id'],
                'type' => $this->processingType
            ]);
            
        } catch (\Exception $e) {
            Log::error("Audio processing failed", [
                'audio_file_id' => $this->audioFile->id,
                'error' => $e->getMessage()
            ]);
            
            $this->audioFile->update([
                'processing_status' => 'failed',
                'error_message' => $e->getMessage()
            ]);
            
            throw $e;
        }
    }
}
```

### 4. Callback Controller

```php
<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\AudioFile;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class AudioCallbackController extends Controller
{
    public function processedCallback(Request $request, AudioFile $audioFile)
    {
        $data = $request->validate([
            'task_id' => 'required|string',
            'status' => 'required|string|in:completed,failed',
            'processing_type' => 'required|string|in:features,stems',
            'storage_paths' => 'required|array',
            'analysis_summary' => 'nullable|array',
            'error_message' => 'nullable|string',
            'processing_time' => 'required|numeric',
            'storage_type' => 'required|string'
        ]);
        
        try {
            $updateData = [
                'processing_status' => $data['status'],
                'processing_time' => $data['processing_time'],
                'storage_type' => $data['storage_type']
            ];
            
            if ($data['status'] === 'completed') {
                $updateData['processed_at'] = now();
                
                // Store analysis results
                if (isset($data['analysis_summary'])) {
                    $updateData['analysis_results'] = $data['analysis_summary'];
                }
                
                // Store processed file paths
                if (isset($data['storage_paths'])) {
                    $updateData['processed_paths'] = $data['storage_paths'];
                }
                
            } elseif ($data['status'] === 'failed') {
                $updateData['error_message'] = $data['error_message'] ?? 'Processing failed';
            }
            
            $audioFile->update($updateData);
            
            // Dispatch any follow-up events
            if ($data['status'] === 'completed') {
                event(new \App\Events\AudioProcessingCompleted($audioFile));
            }
            
            Log::info("Audio processing callback received", [
                'audio_file_id' => $audioFile->id,
                'task_id' => $data['task_id'],
                'status' => $data['status']
            ]);
            
            return response()->json(['status' => 'success']);
            
        } catch (\Exception $e) {
            Log::error("Callback processing failed", [
                'audio_file_id' => $audioFile->id,
                'error' => $e->getMessage()
            ]);
            
            return response()->json([
                'status' => 'error',
                'message' => 'Failed to process callback'
            ], 500);
        }
    }
}
```

### 5. Configuration

```php
// config/audio.php
return [
    'microservice_url' => env('AUDIO_MICROSERVICE_URL', 'http://localhost:8001'),
    // Must match the storage type configured in microservice
    'storage_disk' => env('AUDIO_STORAGE_DISK', 'private'), // Use 'private' disk for local, 'r2' for cloud
    'supported_formats' => ['wav', 'mp3', 'flac', 'm4a', 'ogg'],
    'max_file_size' => env('AUDIO_MAX_FILE_SIZE', 104857600), // 100MB
    'timeout' => [
        'status_check' => env('AUDIO_TIMEOUT_STATUS', 10),
        'processing' => env('AUDIO_TIMEOUT_PROCESSING', 30),
        'batch' => env('AUDIO_TIMEOUT_BATCH', 60)
    ]
];
```

And in your Laravel `.env`:
```bash
# Audio Processing Configuration
AUDIO_MICROSERVICE_URL=http://localhost:8001
AUDIO_STORAGE_DISK=private
AUDIO_MAX_FILE_SIZE=104857600
AUDIO_TIMEOUT_STATUS=10
AUDIO_TIMEOUT_PROCESSING=30
AUDIO_TIMEOUT_BATCH=60

# For local storage, ensure both services use same private path
# Laravel uses: storage/app/private/ (via 'private' disk)
# Microservice needs: LOCAL_STORAGE_PATH=/full/path/to/laravel/storage/app/private

# For R2 storage, both services use same R2 configuration
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET=forge-audio
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://forge-audio.your-account-id.r2.dev
```

You'll also need to add the 'private' disk to your Laravel `config/filesystems.php`:
```php
'disks' => [
    // ... existing disks
    
    'private' => [
        'driver' => 'local',
        'root' => storage_path('app/private'),
        'visibility' => 'private',
        'throw' => false,
    ],
],
```

### 6. Database Migration

```php
// database/migrations/create_audio_files_table.php
Schema::create('audio_files', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->onDelete('cascade');
    $table->string('original_filename');
    $table->string('storage_path');
    $table->bigInteger('file_size');
    $table->string('mime_type');
    $table->string('microservice_task_id')->nullable();
    $table->enum('processing_status', ['pending', 'processing', 'completed', 'failed'])->default('pending');
    $table->enum('processing_type', ['features', 'stems'])->nullable();
    $table->json('analysis_results')->nullable();
    $table->json('processed_paths')->nullable();
    $table->float('processing_time')->nullable();
    $table->string('storage_type')->nullable();
    $table->text('error_message')->nullable();
    $table->timestamp('processed_at')->nullable();
    $table->timestamps();
    
    $table->index(['user_id', 'processing_status']);
    $table->index('microservice_task_id');
});
```

## Callback Data Format

The microservice sends callbacks using the `StorageCallbackData` model format:

### Feature Extraction Callback
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "completed",
    "processing_type": "features",
    "storage_paths": {
        "analysis": "processed/123/2025/08/13/uuid_features.json",
        "processed": "processed/123/2025/08/13/uuid_processed.wav"
    },
    "analysis_summary": {
        "bpm": 120.5,
        "key": "C major",
        "key_confidence": 0.82,
        "loudness_db": -12.3,
        "brightness": 2000.0,
        "duration": 180.0
    },
    "processing_time": 3.45,
    "storage_type": "local"
}
```

### Stem Separation Callback
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "completed",
    "processing_type": "stems",
    "storage_paths": {
        "vocals": "stems/123/2025/08/13/uuid/vocals.wav",
        "drums": "stems/123/2025/08/13/uuid/drums.wav",
        "bass": "stems/123/2025/08/13/uuid/bass.wav",
        "other": "stems/123/2025/08/13/uuid/other.wav"
    },
    "processing_time": 45.67,
    "storage_type": "local"
}
```

### Failed Processing Callback
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "failed",
    "processing_type": "features",
    "storage_paths": {},
    "error_message": "File format not supported",
    "processing_time": 2.1,
    "storage_type": "local"
}
```

### Tempo Processing Callback (NEW)
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "completed",
    "processing_type": "tempo",
    "original_analysis": {
        "bpm": 120.0,
        "duration": 180.0,
        "sample_rate": 44100,
        "key": "C major"
    },
    "tempo_processing": {
        "preset": "nightcore",
        "tempo_factor": 1.4,
        "pitch_shift_semitones": 4.0,
        "preserve_pitch": false,
        "processing_method": "direct",
        "effects_applied": ["tempo_change", "pitch_shift", "brightness_boost"],
        "final_bpm": 168.0,
        "quality_score": 0.9,
        "processing_warnings": []
    },
    "storage_paths": {
        "processed_audio": "processed/123/2025/08/17/song_tempo_nightcore-140-pitch+4.wav",
        "original": "uploads/123/2025/08/15/song.mp3"
    },
    "processing_time": 45.2,
    "storage_type": "local"
}
```

#### Tempo Processing with Warnings
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "completed", 
    "processing_type": "tempo",
    "tempo_processing": {
        "preset": "custom",
        "tempo_factor": 2.5,
        "pitch_shift_semitones": 10.0,
        "preserve_pitch": false,
        "processing_method": "direct",
        "effects_applied": ["tempo_change", "pitch_shift"],
        "final_bpm": 300.0,
        "quality_score": 0.6,
        "processing_warnings": [
            "Very fast tempo may cause audio artifacts",
            "Large pitch shifts may cause unnatural sound",
            "Combining high tempo and pitch changes may degrade quality"
        ]
    },
    "storage_paths": {
        "processed_audio": "processed/456/2025/08/17/track_tempo_custom-250-pitch+10.wav",
        "original": "uploads/456/2025/08/15/track.wav"
    },
    "processing_time": 120.5,
    "storage_type": "local"
}
```

### Batch Processing Callback
```json
{
    "task_id": "batch-abc123-def456",
    "status": "completed",
    "processing_type": "features",
    "storage_paths": {
        "batch_results": [
            {
                "storage_path": "uploads/123/2025/01/01/song1.wav",
                "analysis_path": "processed/123/2025/01/01/song1_features.json",
                "status": "completed"
            },
            {
                "storage_path": "uploads/123/2025/01/01/song2.wav",
                "analysis_path": "processed/123/2025/01/01/song2_features.json",
                "status": "completed"
            }
        ]
    },
    "analysis_summary": {
        "batch_id": "batch_123",
        "processed_count": 2,
        "failed_count": 0,
        "total_duration": 360.5
    },
    "processing_time": 12.3,
    "storage_type": "local"
}
```

## File Naming Conventions

### Tempo Processing Files (NEW)

The microservice now generates descriptive filenames for tempo processed audio instead of UUIDs:

#### Filename Pattern
```
{basename}_tempo_{preset}-{tempo_percentage}[-pitch{±semitones}].wav
```

#### Examples
- **Nightcore**: `my-song_tempo_nightcore-140-pitch+4.wav`
  - Original: `my-song.mp3`
  - Preset: nightcore (1.4x speed, +4 semitones pitch)
  
- **Sped Up**: `track_tempo_sped-up-125.wav` 
  - Original: `track.wav`
  - Preset: sped_up (1.25x speed, no pitch change)
  
- **Slowed Reverb**: `chill-song_tempo_slowed-reverb-75-pitch-2.wav`
  - Original: `chill-song.flac` 
  - Preset: slowed_reverb (0.75x speed, -2 semitones)
  
- **Custom**: `vocal-track_tempo_custom-80.wav`
  - Original: `vocal-track.ogg`
  - Custom settings (0.8x speed, no pitch change)

#### Key Features
- **Descriptive**: File names clearly indicate processing applied
- **Consistent**: All tempo files follow same pattern
- **Laravel-Compatible**: Fits existing storage path structure
- **Informative**: Tempo percentage and pitch shift clearly visible

### Storage Path Structure

Processed tempo files maintain the user-based folder structure:
```
processed/{user_id}/YYYY/MM/DD/{descriptive_filename}.wav
```

Example:
```
processed/123/2025/08/17/my-song_tempo_nightcore-140-pitch+4.wav
```

## Workflow Examples

### Basic Feature Extraction
1. User uploads audio file via Laravel
2. Laravel stores file to configured storage (local/R2) using user-based path structure
3. Laravel queues `ProcessAudioFileJob` with type 'features'
4. Job calls microservice `POST /storage/extract-features` with callback URL
5. Microservice processes file asynchronously using Celery task queue
6. Microservice sends callback to Laravel with `StorageCallbackData` format
7. Laravel updates database with analysis results and notifies user

### Stem Separation
1. User requests stem separation from Laravel
2. Laravel queues `ProcessAudioFileJob` with type 'stems'
3. Job calls microservice `POST /storage/separate-stems` with callback URL
4. Microservice separates audio into stems (vocals, drums, bass, other)
5. Microservice uploads stems to storage using user-based folder structure
6. Microservice sends callback with stem storage paths
7. Laravel updates database and provides download links to user

### Batch Processing
1. User selects multiple files for batch processing
2. Laravel calls microservice `POST /storage/batch-process`
3. Microservice queues individual tasks for each file
4. Microservice processes files concurrently
5. Microservice sends single callback with batch results
6. Laravel updates all file records and notifies user

### Tempo Processing (NEW)
1. User requests tempo modification from Laravel
2. Laravel calls microservice `POST /tempo/storage/process` with descriptive parameters
3. Microservice processes audio with specified preset and parameters
4. Microservice generates descriptive filename and uploads to storage
5. Microservice sends enhanced callback with complete tempo_processing metadata
6. Laravel receives callback with:
   - **Descriptive filename** in `storage_paths.processed_audio`
   - **Complete processing details** in `tempo_processing` object
   - **Quality metrics** including `quality_score` and `processing_warnings`
   - **Original analysis** with BPM, key, duration
7. Laravel updates database and provides download link with meaningful filename

### Task Monitoring
1. Laravel receives task_id from microservice
2. Laravel can poll `GET /task/summary/{task_id}` for lightweight status
3. For full details, Laravel can call `GET /task/status/{task_id}` or `GET /task/result/{task_id}`
4. Failed or stuck tasks can be cleaned up with `DELETE /task/{task_id}`

## Error Handling

- Always validate microservice responses
- Implement retry logic for transient failures
- Log all microservice interactions
- Provide meaningful error messages to users
- Monitor task status for stuck processes

## Performance Considerations

- Use async processing for all audio operations (recommended for Laravel integration)
- Implement proper queue management in both Laravel and Celery
- Monitor storage usage and implement cleanup policies
- Set appropriate timeouts (status: 10s, processing: 30s, batch: 60s)
- Use `/task/summary/{task_id}` instead of full result endpoints for better performance
- Cache task results when possible
- Use batch processing for multiple files to reduce API calls
- Monitor tempo processing cache hit rates via `/tempo/performance/metrics`

## Security

- Validate all callback data
- Implement proper authentication between services
- Sanitize file paths and names
- Use HTTPS for all communications
- Regularly rotate API keys and secrets

## Monitoring

- Track processing times
- Monitor failure rates
- Alert on storage capacity
- Log performance metrics
- Monitor queue depths