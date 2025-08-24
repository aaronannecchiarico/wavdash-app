# Cloudflare R2 Integration Guide

This document outlines the complete integration between the Laravel Beat Forge application and Cloudflare R2 storage using a **two-bucket architecture** for private and public files, including the audio analysis microservice integration.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────┐    ┌──────────────────────┐    ┌─────────────────────────┐
│          Laravel App            │    │   Audio Microservice │    │    Cloudflare R2        │
│                                 │    │      (FastAPI)       │    │                         │
│ ┌─────────────────────────────┐ │    │ ┌──────────────────┐ │    │ ┌─────────────────────┐ │
│ │      Upload Controller      │ │    │ │  Audio Analysis  │ │    │ │   audio-private     │ │
│ │   (Saves to private bucket) │ │    │ │   /extract-      │ │    │ │   (Private Access)  │ │
│ └─────────────────────────────┘ │    │ │   features       │ │    │ │                     │ │
│ ┌─────────────────────────────┐ │    │ └──────────────────┘ │    │ │ Original uploads:   │ │
│ │   ProcessAudioUpload Job    │ │    │ ┌──────────────────┐ │    │ │ /uploads/{uid}/     │ │
│ │   (Converts & publishes)    │ │    │ │   Callbacks      │ │    │ │ /{Y/m/d}/file       │ │
│ └─────────────────────────────┘ │    │ │   /callback      │ │    │ │                     │ │
│ ┌─────────────────────────────┐ │    │ └──────────────────┘ │    │ │ Processed files:    │ │
│ │   AudioAnalysisService      │◄──── │                      │    │ │ /processed/{uid}/   │ │
│ │   (Smart routing R2/local)  │ │    │                      │    │ │ /{Y/m/d}/file       │ │
│ └─────────────────────────────┘ │    │                      │    │ │                     │ │
│ ┌─────────────────────────────┐ │    │                      │    │ │ Stem files:         │ │
│ │     R2StorageService        │◄──── │                      │◄──── │ /stems/{uid}/       │ │
│ │   (Dual-bucket support)    │ │    │                      │    │ │ /{Y/m/d}/file       │ │
│ └─────────────────────────────┘ │    │                      │    │ └─────────────────────┘ │
│ ┌─────────────────────────────┐ │    │                      │    │ ┌─────────────────────┐ │
│ │ PublishToPublicBucket Job   │ │    │                      │    │ │   audio-public      │ │
│ │   (Copies to public bucket) │ │    │                      │    │ │   (Public Access)   │ │
│ └─────────────────────────────┘ │    │                      │    │ │                     │ │
└─────────────────────────────────┘    └──────────────────────┘    │ │ Stream files:       │ │
                                                                   │ │ /stream/{uid}/      │ │
                                                                   │ │ /{Y/m/d}/file.ogg   │ │
                                                                   │ │                     │ │
                                                                   │ │ Public stems:       │ │
                                                                   │ │ /stems/{uid}/       │ │
                                                                   │ │ /{Y/m/d}/file.wav   │ │
                                                                   │ └─────────────────────┘ │
                                                                   └─────────────────────────┘
```

## 🔧 Configuration

### Laravel Environment Variables

```env
# Storage Configuration (set to 'r2' to enable R2 storage)
FILESYSTEM_DISK=local  # or 'r2' for R2 storage

# Cloudflare R2 Configuration - Two Bucket Setup
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key

# Private Bucket (for original uploads, processed files, stems - access controlled)
R2_PRIVATE_BUCKET=audio-private
R2_PRIVATE_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com

# Public Bucket (for streaming files - publicly accessible)
R2_PUBLIC_BUCKET=audio-public
R2_PUBLIC_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://audio-public.your-account-id.r2.dev

# Audio Analysis Configuration
AUDIO_ANALYSIS_BASE_URL=http://localhost:8001
AUDIO_ANALYSIS_ENABLED=true
AUDIO_ANALYSIS_R2_INTEGRATION_ENABLED=true
```

## 🗄️ Two-Bucket Storage Strategy

### Private Bucket (`audio-private`)
- **Access**: Private, only accessible via API credentials
- **Purpose**: Store sensitive files that should not be publicly accessible
- **Contents**:
  - Original uploaded files: `/uploads/{user_id}/{Y/m/d}/filename`
  - Processed files: `/processed/{user_id}/{Y/m/d}/filename`
  - Stem files: `/stems/{user_id}/{Y/m/d}/stem_type.wav`
  - Analysis data files: `/analysis/{user_id}/{Y/m/d}/analysis.json`

### Public Bucket (`audio-public`)
- **Access**: Public via r2.dev URL for streaming
- **Purpose**: Store files that need to be publicly accessible for frontend playback
- **Contents**:
  - Streaming files: `/stream/{user_id}/{Y/m/d}/filename.ogg`
  - Public stems: `/stems/{user_id}/{Y/m/d}/stem_type.wav` (when user chooses to share)
  - Tempo files: `/tempo/{user_id}/{Y/m/d}/tempo_adjusted.ogg`

### File Flow Between Buckets

```
Upload → Private Bucket (audio-private)
       ↓
   Processing (FFmpeg conversion)
       ↓
Stream File → Public Bucket (audio-public) via PublishToPublicBucket Job
Stems → Stay in Private Bucket (unless user shares)
```

### Current Integration Status

**✅ Implemented:**
- Two-bucket R2 storage configuration via `FILESYSTEM_DISK=r2`
- Private bucket for original uploads, processed files, and stems
- Public bucket for streaming files and shared content
- User-organized file structure: `uploads/{user_id}/{Y/m/d}/filename`
- Audio analysis microservice integration with dual R2 bucket support
- Automatic storage detection and smart routing between buckets
- PublishToPublicBucket job for selective file publishing

**🔄 Storage Logic:**
- **Private First**: All uploads go to private bucket initially
- **Selective Publishing**: Only streaming files are copied to public bucket
- **Fallback**: R2 failures automatically fall back to local storage during upload
- **Consistency**: Once a file is in R2, all related processing stays in R2 with appropriate bucket selection

### Microservice Configuration

Your microservice should have matching R2 configuration and the following endpoints available:

- `GET /status` - Service health check
- `POST /extract-features` - Audio analysis (handles both R2 and file upload)
- `POST /callback/{upload_id}` - Analysis completion callback to Laravel

**R2 Integration in Microservice:**
The microservice automatically detects R2 files when Laravel sends the R2 path and credentials. It can process files directly from R2 without needing file uploads.

## 🚀 Current Storage & Processing Flow

### 1. Upload Processing (Two-Bucket Implementation)

**When FILESYSTEM_DISK=r2:**
```
User Upload → UploadController.store()
            ↓
            Store to Private R2 Bucket (audio-private):
            uploads/{user_id}/{Y/m/d}/filename
            ↓
            ProcessAudioUpload Job:
            - Validate storage compatibility (if analysis enabled)
            - Download from R2 private bucket to temp file
            - Convert with FFmpeg (to OGG)
            - Save processed file to private bucket:
              processed/{user_id}/{Y/m/d}/filename.ogg
            ↓
            PublishToPublicBucket Job:
            - Copy streaming file to Public R2 Bucket (audio-public):
              stream/{user_id}/{Y/m/d}/filename.ogg
            - Update Upload model with public stream path
            ↓
            Update Upload model with all R2 paths
```

**When FILESYSTEM_DISK=local:**
```
User Upload → UploadController.store()
            ↓
            Store to local private storage:
            storage/app/private/uploads/{user_id}/{Y/m/d}/filename
            ↓
            ProcessAudioUpload Job:
            - Validate storage compatibility (if analysis enabled)
            - Convert with FFmpeg (to OGG)
            - Save to public storage:
              storage/app/public/uploads/stream/{user_id}/{Y/m/d}/filename.ogg
            ↓
            Update Upload model with local paths
```

### 2. Audio Analysis Flow (Microservice Integration)

**R2 Files:**
```
Analysis Request → AudioAnalysisService.submitForAnalysis()
                ↓ (detects R2 storage)
                POST /extract-features with R2 credentials
                ↓
                Microservice downloads directly from R2
                ↓
                Analysis processing in microservice
                ↓
                POST /callback/{upload_id} to Laravel
                ↓
                Results stored in UploadAnalysis model
```

**Local Files:**
```
Analysis Request → AudioAnalysisService.submitForAnalysis()
                ↓ (detects local storage)
                POST /extract-features with file upload
                ↓
                Traditional file upload to microservice
                ↓
                Analysis processing in microservice
                ↓
                POST /callback/{upload_id} to Laravel
                ↓
                Results stored in UploadAnalysis model
```

## 📡 API Endpoints

### Laravel Routes

**Analysis Management:**
- `POST /uploads/{upload}/analysis` - Start analysis (redirects back with flash message)
- `GET /uploads/{upload}/analysis` - Analysis page (Inertia: `uploads/analysis`)
- `DELETE /uploads/{upload}/analysis` - Delete analysis (redirects back with flash message)
- `GET /uploads/{upload}/analysis/similar` - Similar tracks page (Inertia: `uploads/similar`)

**API Endpoints:**
- `POST /api/analysis/callback/{upload}` - Analysis completion callback from microservice
- `GET /api/analysis/status` - Service status check

### Service Status Response

**Example Response:**
```json
{
  "enabled": true,
  "available": true,
  "r2_integration_enabled": true,
  "base_url": "http://localhost:8001"
}
```

**Status Fields:**
- `enabled`: Audio analysis feature enabled in Laravel
- `available`: Microservice is reachable and responding
- `r2_integration_enabled`: R2 integration enabled for microservice
- `base_url`: Microservice endpoint URL

### Storage Status Endpoint

**Endpoint:** `GET /storage/status`

**Example Response:**
```json
{
  "enabled": true,
  "storage_type": "r2",
  "message": "R2 storage is enabled and ready"
}
```

**Response Fields:**
- `enabled`: Storage system is enabled and operational
- `storage_type`: Current storage type ("r2", "local", etc.)
- `message`: Human-readable status message

**Usage in Laravel:**
The ProcessAudioUpload job automatically validates storage compatibility before processing uploads when audio analysis is enabled. This ensures Laravel and the microservice are using the same storage backend.

## 🗃️ Database Schema

### Upload Model Fields

```php
// Core upload fields
'user_id' => 'integer',                       // Owner of the upload
'title' => 'string',                          // User-defined title
'description' => 'text|nullable',             // Optional description
'filename' => 'string',                       // Original filename
'path' => 'string',                           // Storage path (local or R2)
'stream_path' => 'string|nullable',           // Processed streaming file path
'mime_type' => 'string',                      // File MIME type
'size' => 'bigInteger',                       // File size in bytes
'status' => 'string',                         // pending, processing, ready, failed
'duration_seconds' => 'integer|nullable',     // Audio duration

// R2-specific fields (added in migration)
'r2_upload_path' => 'string|nullable',        // Path in R2 storage
'r2_stems_paths' => 'json|nullable',          // Array of stem file paths in R2
'r2_analysis_path' => 'string|nullable',      // Analysis result path in R2
'r2_uploaded_at' => 'timestamp|nullable',     // R2 upload timestamp
'uses_r2_storage' => 'boolean|default:false', // Storage type flag
```

### Analysis Tables

**UploadAnalysisTask:**
- Tracks analysis job status and metadata
- Links to Upload via `upload_id`
- Stores task ID for microservice communication

**UploadAnalysis:**
- Stores completed analysis results
- Musical features: key, BPM, loudness, brightness, etc.
- Links to Upload via `upload_id`

## 🔍 Key Classes & Methods

### AudioAnalysisService (Primary Integration Point)

```php
$analysisService = app(AudioAnalysisService::class);

// Service status and health checks
$analysisService->isServiceAvailable();          // Check if microservice is available
$analysisService->getServiceStatus();            // Complete status array

// Storage validation
$analysisService->validateStorageCompatibility($upload); // Validate Laravel/microservice storage match

// Analysis submission (automatically routes based on storage type)
$analysisService->submitForAnalysis($upload);    // Smart routing: R2 vs local

// Analysis data retrieval
$analysisService->findSimilarTracks($upload, $limit); // Find similar tracks
```

### R2StorageService (Migration & Management)

```php
$r2Service = app(R2StorageService::class);

// Configuration checks
$r2Service->isEnabled();                          // Check if R2 is configured

// File operations
$r2Service->uploadFile($file, 'uploads');        // Upload file to R2
$r2Service->getFile($path);                      // Download file content
$r2Service->deleteFile($path);                   // Delete file from R2

// Migration tools
$r2Service->migrateUpload($upload);              // Migrate existing upload to R2

// URL generation
$r2Service->getPublicUrl($path);                 // Get public R2 URL
```

### PublishToPublicBucket Job (Two-Bucket Integration)

```php
use App\Jobs\PublishToPublicBucket;

// Dispatch job to copy streaming file from private to public bucket
PublishToPublicBucket::dispatch(
    $upload,                                      // Upload model instance
    'processed/user/2025/08/22/stream.ogg',      // Private bucket path
    'stream/user/2025/08/22/stream.ogg',         // Public bucket path
    'stream'                                     // File type (stream, stem, tempo)
);

// Job automatically:
// - Downloads file from private R2 bucket (audio-private)
// - Uploads file to public R2 bucket (audio-public)
// - Updates Upload model with public path
// - Handles different file types (stream, stem, tempo)
// - Provides comprehensive logging and error handling
```

### Upload Model Helper Methods

```php
// Storage type detection
$upload->usesR2Storage();                        // Check if using R2 storage

// Path resolution (handles both local and R2)
$upload->getFilePath();                          // Get appropriate file path  
$upload->getStreamPath();                        // Get appropriate stream URL (with R2 URL if needed)

// R2-specific checks
$upload->hasR2Stems();                          // Check for R2 stem files

// Analysis relationships
$upload->hasAnalysis();                         // Check if analysis exists
$upload->isAnalysisInProgress();               // Check if analysis is processing
```

## 🛠️ Management Commands

### Storage Management

```bash
# Clear all upload files from storage (local, public, R2)
php artisan uploads:clear

# Force clear without confirmation
php artisan uploads:clear --force

# Database operations (includes automatic storage cleanup)
php artisan migrate:fresh --seed
php artisan migrate:rollback
```

### Migration Commands (if R2StorageService migration tools are implemented)

```bash
# Migrate existing uploads to R2 (dry run)
php artisan uploads:migrate-to-r2 --dry-run --limit=10

# Actually migrate uploads to R2
php artisan uploads:migrate-to-r2 --limit=10
```

## 🧪 Testing the Integration

### 1. Test Configuration

```bash
# Check current storage configuration
php artisan tinker --execute="
echo 'Default disk: ' . config('filesystems.default') . PHP_EOL;
echo 'Analysis enabled: ' . (config('services.audio_analysis.enabled') ? 'true' : 'false') . PHP_EOL;
echo 'R2 integration enabled: ' . (config('services.audio_analysis.r2_integration_enabled') ? 'true' : 'false') . PHP_EOL;
"
```

### 2. Test Service Status

```bash
# Check Laravel analysis service status
curl http://localhost:8000/api/analysis/status

# Check microservice health directly
curl http://localhost:8001/status
```

### 3. R2 Storage Test

1. **Enable R2**: Set `FILESYSTEM_DISK=r2` in `.env`
2. **Configure R2**: Set R2 credentials in `.env`
3. **Upload Test**: Upload an audio file via the web interface
4. **Check Logs**: Look for R2 upload confirmation in logs
5. **Verify Storage**: Check that files appear in R2 bucket with user-organized structure
6. **Test Processing**: Verify ProcessAudioUpload job completes successfully

### 4. Analysis Workflow Test

1. **Upload file** (local or R2)
2. **Navigate** to upload show page
3. **Click "Analyze"** to start analysis
4. **Check logs** for analysis submission
5. **Wait for callback** from microservice
6. **Verify results** appear in analysis page

### 5. Local Fallback Test

1. **Misconfigure R2** (wrong credentials)
2. **Upload file** - should fall back to local storage
3. **Check logs** for fallback confirmation
4. **Verify** upload still works with local storage

## 🔄 Current Storage Decision Logic

### Storage Selection (Upload Time)

```
Upload Request
├── FILESYSTEM_DISK=r2?
│   ├── YES: Try R2 upload
│   │   ├── SUCCESS: uses_r2_storage=true, store r2_upload_path
│   │   └── FAILURE: Fallback to local storage, uses_r2_storage=false
│   └── NO: Use local storage, uses_r2_storage=false
```

### Processing Logic

```
ProcessAudioUpload Job
├── upload.usesR2Storage()?
│   ├── YES: R2 Processing
│   │   ├── Download from R2 to temp file
│   │   ├── Convert with FFmpeg
│   │   └── Upload processed file back to R2
│   └── NO: Local Processing
│       ├── Convert with FFmpeg from local storage
│       └── Save processed file to local public storage
```

### Analysis Routing

```
Analysis Request
├── upload.usesR2Storage()?
│   ├── YES: Send R2 credentials to microservice
│   │   └── Microservice downloads directly from R2
│   └── NO: Upload file to microservice
│       └── Traditional file upload workflow
```

## 🚨 Current Implementation Notes

1. **Consistent Storage**: Once a file is in R2, all related processing stays in R2
2. **Automatic Fallback**: R2 failures fall back to local storage during upload
3. **User-Organized Structure**: Both R2 and local use `/uploads/{user_id}/{Y/m/d}/` structure
4. **Smart Analysis Routing**: AudioAnalysisService automatically detects storage type
5. **Comprehensive Cleanup**: Migration rollbacks clear both local and R2 storage
6. **Frontend Integration**: Upload model methods handle URL generation for both storage types
7. **Fixed Storage Detection**: ProcessAudioUpload job now correctly processes files based on `upload.usesR2Storage()` rather than default filesystem configuration
8. **Storage Validation**: ProcessAudioUpload job validates Laravel/microservice storage compatibility before processing (when audio analysis is enabled)

## 🛠️ Recent Fixes

### ProcessAudioUpload Storage Detection (Fixed 2025-08-21)

**Issue**: When `FILESYSTEM_DISK=local` but uploads used R2 storage (`uses_r2_storage=true`), the ProcessAudioUpload job incorrectly tried to process files from local storage instead of R2.

**Root Cause**: Job was checking `config('filesystems.default') === 'r2'` instead of `upload.usesR2Storage()`.

**Fix**: Updated ProcessAudioUpload logic to use upload's actual storage type:

```php
// OLD (broken): Required default disk to be 'r2'
if ($this->upload->usesR2Storage() && $disk === 'r2') {
    // R2 processing...
}

// NEW (fixed): Uses upload's actual storage type
if ($this->upload->usesR2Storage()) {
    // R2 processing...
}
```

**Testing**: Added comprehensive tests in `ProcessAudioUploadStorageTest.php` to verify storage switching works correctly regardless of default filesystem configuration.

### Storage Validation Implementation (Added 2025-08-21)

**Feature**: Added storage compatibility validation between Laravel and the audio analysis microservice before processing uploads.

**Implementation**:
- New `validateStorageCompatibility()` method in `AudioAnalysisService`
- Automatic validation in `ProcessAudioUpload` job when audio analysis is enabled
- Validates that Laravel and microservice use the same storage backend (r2 vs local)
- Logs validation results and continues processing even if validation fails (non-blocking)

**Key Benefits**:
- Prevents storage type mismatches that could cause processing failures
- Provides early warning when storage configurations are out of sync
- Maintains backward compatibility by being non-blocking

**Testing**: Added comprehensive tests in `StorageValidationTest.php` covering all validation scenarios including success, failure, and microservice unavailability cases.

### FFMpeg Path Resolution Fix (2025-08-21)

**Issue**: FFMpeg was incorrectly prepending Laravel's storage app path to absolute temporary file paths when processing R2 files.

**Error**: `FFMpeg cannot find "/Users/.../storage/app/var/folders/.../T/..."`

**Root Cause**: `FFMpeg::open($tempFilePath)` expects relative paths within a filesystem disk, not absolute paths. When processing R2 files, the job downloads to a temporary file with an absolute path, but Laravel FFMpeg was treating it as relative to the app storage directory.

**Solution**: Created custom filesystem adapter using root directory as base, allowing absolute paths to be treated as relative paths from root:

```php
// Create a filesystem instance that uses root directory as base
$adapter = new LocalFilesystemAdapter('/');
$flysystemFilesystem = new Filesystem($adapter);
$filesystem = new FilesystemAdapter($flysystemFilesystem, $adapter, []);

// Remove leading slash to make it relative to root
$relativePath = ltrim($tempFilePath, '/');
$ffmpeg = FFMpeg::fromFilesystem($filesystem)->open($relativePath);
```

**Key Benefits**:
- Fixes path resolution for R2 temporary files
- Maintains compatibility with Laravel FFMpeg API
- No impact on local storage processing
- Proper error handling for FFMpeg operations

**Testing**: Added comprehensive test suite in `ProcessAudioUploadFFMpegTest.php` to verify:
- Temporary file path conversion works correctly
- FFMpeg no longer receives Laravel storage path prefixes
- R2 file download and processing workflow
- Path resolution errors are eliminated

## 📊 Monitoring & Debugging

### Log Entries to Watch

**Upload Processing:**
```bash
# Upload Controller
"Upload Controller - Starting file upload" with user_id, filename, target_path
"Upload Controller - File stored successfully" with stored_path, storage_disk

# ProcessAudioUpload Job
"ProcessAudioUpload - Starting job" with upload_id, storage type
"ProcessAudioUpload - Storage compatibility validated successfully" with validation_message
"ProcessAudioUpload - Storage compatibility validation failed" with validation_result (warning)
"ProcessAudioUpload - Configuration" with disk, paths, file existence
"ProcessAudioUpload - FFmpeg opened successfully"
"Audio file processed successfully"
```

**Analysis Workflow:**
```bash
# Analysis submission
"AudioAnalysisService - Submitting for analysis" with upload_id, storage_type
"Audio analysis task submitted" with task_id

# Callback processing
"AudioAnalysisService - Analysis callback received" with upload_id
"AudioAnalysisService - Analysis results saved"
```

**R2 Operations:**
```bash
# R2 upload (when FILESYSTEM_DISK=r2)
"File uploaded to R2" with r2_path
"ProcessAudioUpload - R2 export completed"

# R2 download for processing
"ProcessAudioUpload - Starting R2 download"
"File downloaded from R2 to temp"
```

### Key Performance Indicators

- **Upload Success Rate**: Monitor upload completion vs failures
- **Processing Time**: Audio conversion job completion time
- **Analysis Success Rate**: Microservice analysis completion
- **Storage Distribution**: Percentage of files in R2 vs local
- **Service Availability**: Microservice uptime and response time

### Troubleshooting Common Issues

**Upload Failures:**
1. Check storage permissions and disk space
2. Verify R2 credentials if using R2 storage
3. Review ProcessAudioUpload job logs for FFmpeg errors

**Analysis Failures:**
1. Verify microservice is running and accessible
2. Check R2 credentials match between Laravel and microservice
3. Monitor callback endpoint for proper responses

**R2 Integration Issues:**
1. Test R2 connectivity: `php artisan tinker` with Storage::disk('r2')->exists('test')`
2. Verify user-organized path structure in R2 bucket
3. Check public URL configuration for R2 streaming

This integration provides a robust, scalable solution for audio file management with seamless R2 cloud storage integration and intelligent local fallback mechanisms.