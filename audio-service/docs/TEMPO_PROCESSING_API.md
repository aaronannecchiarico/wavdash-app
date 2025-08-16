# Tempo Processing API Documentation

## Overview

The Tempo Processing API provides advanced sped-up and slowed-down audio effects that are popular on social media platforms like TikTok and Instagram. It supports various presets including chipmunk effects, slowed + reverb, nightcore, and chopped & screwed styles.

## Features

- **Multiple Processing Modes**: Direct upload, storage-based processing, and synchronous processing
- **Popular Presets**: Sped-up, slowed + reverb, nightcore, chopped & screwed styles
- **Stem-Based Processing**: Individual processing of vocals, drums, bass, and other components for higher quality
- **Smart BPM Integration**: Intelligent preset suggestions based on detected BPM
- **Performance Optimization**: Advanced caching for faster processing of similar requests
- **Laravel Integration**: Seamless integration with Laravel applications via callbacks

## Authentication

All tempo processing endpoints use the same authentication as the main API. Include your API key in the request headers:

```http
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### 1. Direct File Upload Processing

#### Process Tempo (Async)
```http
POST /tempo/process
Content-Type: multipart/form-data
```

**Parameters:**
- `audio_file` (file, required): Audio file to process (MP3, WAV, FLAC, etc.)
- `preset` (string, optional): Processing preset (default: "custom")
- `tempo_factor` (float, optional): Tempo multiplier 0.25-4.0 (default: 1.0)
- `pitch_shift_semitones` (float, optional): Pitch shift in semitones -12 to +12 (default: 0.0)
- `preserve_pitch` (boolean, optional): Whether to preserve original pitch (default: false)
- `add_reverb` (boolean, optional): Add reverb effect (default: false)
- `use_stems` (boolean, optional): Process stems separately for higher quality (default: false)
- `async_processing` (boolean, optional): Process asynchronously (default: true)

**Example Request:**
```bash
curl -X POST "http://localhost:8001/tempo/process" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "audio_file=@song.mp3" \
  -F "preset=slowed_reverb" \
  -F "use_stems=true"
```

**Response:**
```json
{
  "task_id": "abc123-def456-789xyz",
  "status": "processing",
  "message": "Tempo processing started for song.mp3 with preset 'slowed_reverb'",
  "estimated_completion": "2025-08-16T10:35:00Z"
}
```

#### Process Tempo (Sync)
```http
POST /tempo/process-sync
Content-Type: multipart/form-data
```

Same parameters as async endpoint, but returns processed audio immediately. Recommended only for short audio files (< 60 seconds).

### 2. Storage-Based Processing (Recommended for Laravel)

#### Process from Storage
```http
POST /tempo/storage/process
Content-Type: application/json
```

**Request Body:**
```json
{
  "storage_path": "uploads/user_123/2025/08/16/song.mp3",
  "preset": "slowed_reverb",
  "tempo_factor": 0.75,
  "pitch_shift_semitones": -2,
  "preserve_pitch": false,
  "add_reverb": true,
  "use_stems": true,
  "callback_url": "https://yourapp.com/api/tempo-callback",
  "metadata": {
    "user_id": "123",
    "upload_id": "456",
    "project_id": "789"
  }
}
```

**Response:**
```json
{
  "task_id": "tempo_abc123-def456",
  "status": "processing",
  "message": "Tempo processing started for uploads/user_123/2025/08/16/song.mp3 with preset 'slowed_reverb'",
  "storage_type": "local",
  "estimated_completion": "2025-08-16T10:35:00Z"
}
```

### 3. Information Endpoints

#### Get Available Presets
```http
GET /tempo/presets
```

**Response:**
```json
{
  "available_presets": {
    "sped_up": {
      "name": "Sped Up",
      "tempo_factor": 1.25,
      "pitch_shift_semitones": 3,
      "preserve_pitch": false,
      "effects": ["pitch_shift", "brightness_boost"],
      "description": "Popular chipmunk effect - faster tempo with higher pitch"
    },
    "slowed_reverb": {
      "name": "Slowed + Reverb",
      "tempo_factor": 0.75,
      "pitch_shift_semitones": -2,
      "preserve_pitch": false,
      "effects": ["pitch_shift", "reverb"],
      "description": "Dreamy slowed-down effect with atmospheric reverb"
    },
    "nightcore": {
      "name": "Nightcore",
      "tempo_factor": 1.4,
      "pitch_shift_semitones": 4,
      "preserve_pitch": false,
      "effects": ["pitch_shift", "brightness_boost", "compression"],
      "description": "Fast tempo with high pitch and enhanced brightness"
    },
    "chopped_screwed": {
      "name": "Chopped & Screwed",
      "tempo_factor": 0.6,
      "pitch_shift_semitones": -3,
      "preserve_pitch": false,
      "effects": ["pitch_shift", "low_pass_filter"],
      "description": "Houston-style slow tempo with low-pass filtering"
    },
    "custom": {
      "name": "Custom",
      "tempo_factor": 1.0,
      "pitch_shift_semitones": 0.0,
      "preserve_pitch": false,
      "effects": [],
      "description": "Custom tempo/pitch settings"
    }
  },
  "default_preset": "custom",
  "tempo_factor_range": {"min": 0.25, "max": 4.0},
  "pitch_shift_range": {"min": -12.0, "max": 12.0},
  "supported_effects": [
    "pitch_shift",
    "reverb",
    "time_stretch",
    "brightness_boost",
    "compression",
    "low_pass_filter"
  ]
}
```

#### Get Smart Preset Suggestions
```http
GET /tempo/suggest-presets?current_bpm=120&duration_seconds=180
```

**Response:**
```json
{
  "status": "success",
  "audio_analysis": {
    "bpm": 120,
    "duration_seconds": 180,
    "classification": "moderate"
  },
  "suggestions": {
    "chill_version": {
      "preset": "slowed_reverb",
      "reason": "Current BPM is moderate - slowed version will create relaxing atmosphere",
      "optimal_factor": 0.75
    },
    "energetic_version": {
      "preset": "sped_up",
      "reason": "Speed up will create energetic, viral-ready version",
      "optimal_factor": 1.3
    },
    "dance_version": {
      "preset": "nightcore",
      "reason": "Nightcore style perfect for dance remixes at this BPM",
      "optimal_factor": 1.4
    }
  }
}
```

### 4. System Information

#### Check System Compatibility
```http
GET /tempo/system/compatibility
```

**Response:**
```json
{
  "status": "success",
  "compatibility": {
    "pedalboard_available": true,
    "librosa_available": true,
    "system_type": "darwin",
    "device_type": "cpu",
    "processing_capabilities": {
      "time_stretching": true,
      "pitch_shifting": true,
      "effects_processing": true,
      "stem_separation": true
    },
    "recommended_settings": {
      "max_file_size_mb": 100,
      "max_duration_seconds": 600,
      "optimal_sample_rate": 44100
    }
  },
  "phase": "Phase 2: Enhanced pedalboard processing available"
}
```

### 5. Performance Monitoring

#### Get Performance Metrics
```http
GET /tempo/performance/metrics
```

**Response:**
```json
{
  "status": "success",
  "timestamp": 1692188400,
  "performance_metrics": {
    "uptime_seconds": 86400,
    "total_requests": 1250,
    "cache_hit_rate_percent": 67.5,
    "error_rate_percent": 2.1,
    "processing_times": {
      "average_seconds": 15.3,
      "median_seconds": 12.1,
      "min_seconds": 3.2,
      "max_seconds": 45.8,
      "p95_seconds": 28.7
    },
    "preset_usage": {
      "slowed_reverb": 450,
      "sped_up": 380,
      "nightcore": 220,
      "custom": 150,
      "chopped_screwed": 50
    },
    "average_file_size_mb": 8.5
  },
  "cache_statistics": {
    "total_files": 1200,
    "audio_cache_files": 800,
    "bpm_cache_files": 250,
    "preset_cache_files": 150,
    "total_size_mb": 245.7,
    "cache_directory": "/tmp/beatforge_cache"
  },
  "recommendations": [
    {
      "type": "performance",
      "priority": "info",
      "message": "Excellent cache hit rate (67.5%). System is well optimized.",
      "action": "No action needed"
    }
  ]
}
```

#### Clear Performance Cache
```http
POST /tempo/performance/cache/clear
Content-Type: application/json
```

**Request Body:**
```json
{
  "cache_type": "all"  // Options: "all", "audio", "bmp", "preset"
}
```

## Processing Response Format

### Completed Processing Response

When processing is complete, you'll receive a comprehensive response:

```json
{
  "task_id": "tempo_abc123-def456",
  "status": "completed",
  "message": "Tempo processing completed successfully",
  "original_analysis": {
    "bpm": 120.5,
    "key": "C major",
    "key_confidence": 0.85,
    "loudness_db": -12.3,
    "brightness": 0.72,
    "duration": 180.0,
    "sample_rate": 44100
  },
  "tempo_processing": {
    "preset": "slowed_reverb",
    "tempo_factor": 0.75,
    "pitch_shift_semitones": -2,
    "preserve_pitch": false,
    "final_bpm": 90.4,
    "processing_method": "stems_separate",
    "effects_applied": ["time_stretch", "pitch_shift", "reverb"],
    "quality_score": 8.7,
    "processing_warnings": []
  },
  "output_files": {
    "processed_audio": "processed/user_123/2025/08/16/song_tempo_slowed_reverb.wav",
    "original_features": "processed/user_123/2025/08/16/song_features.json",
    "stems_processed": {
      "vocals": "processed/user_123/2025/08/16/song_vocals_slowed_reverb.wav",
      "drums": "processed/user_123/2025/08/16/song_drums_slowed_reverb.wav",
      "bass": "processed/user_123/2025/08/16/song_bass_slowed_reverb.wav",
      "other": "processed/user_123/2025/08/16/song_other_slowed_reverb.wav"
    }
  },
  "public_urls": {
    "processed_audio": "https://storage.example.com/processed/user_123/2025/08/16/song_tempo_slowed_reverb.wav",
    "stems_processed": {
      "vocals": "https://storage.example.com/processed/user_123/2025/08/16/song_vocals_slowed_reverb.wav",
      "drums": "https://storage.example.com/processed/user_123/2025/08/16/song_drums_slowed_reverb.wav",
      "bass": "https://storage.example.com/processed/user_123/2025/08/16/song_bass_slowed_reverb.wav",
      "other": "https://storage.example.com/processed/user_123/2025/08/16/song_other_slowed_reverb.wav"
    }
  },
  "smart_suggestions": {
    "alternative_presets": [
      {
        "preset": "nightcore",
        "reason": "For an even more energetic version",
        "confidence": 0.78
      }
    ],
    "optimal_settings": {
      "recommended_tempo_factor": 0.8,
      "reason": "Slightly faster tempo might work better for this genre"
    }
  },
  "processing_time": 45.2,
  "cache_hit": false,
  "storage_type": "local"
}
```

## Laravel Integration

### Setting Up Callbacks

For Laravel applications, use the storage-based processing endpoint with a callback URL:

```php
// Laravel Controller Example
public function processTempoAudio(Request $request)
{
    $uploadedFile = $request->file('audio');
    $userId = auth()->id();
    
    // Store file in shared storage
    $storagePath = Storage::putFile(
        "uploads/{$userId}/" . date('Y/m/d'), 
        $uploadedFile
    );
    
    // Call tempo processing service
    $response = Http::post('http://audio-service:8001/tempo/storage/process', [
        'storage_path' => $storagePath,
        'preset' => $request->input('preset', 'slowed_reverb'),
        'use_stems' => $request->boolean('high_quality', false),
        'callback_url' => route('api.tempo.callback'),
        'metadata' => [
            'user_id' => $userId,
            'upload_id' => $request->input('upload_id'),
            'project_id' => $request->input('project_id')
        ]
    ]);
    
    return response()->json([
        'task_id' => $response->json('task_id'),
        'status' => 'processing',
        'message' => 'Your audio is being processed with tempo effects!'
    ]);
}

// Callback Handler
public function handleTempoCallback(Request $request)
{
    $data = $request->all();
    
    // Update your database with processing results
    AudioProcessingJob::where('task_id', $data['task_id'])
        ->update([
            'status' => $data['status'],
            'result_data' => $data,
            'processed_at' => now()
        ]);
    
    // Notify user if processing completed
    if ($data['status'] === 'completed') {
        // Send notification to user
        // Update file records with new URLs
        // Trigger any additional workflows
    }
    
    return response()->json(['status' => 'received']);
}
```

### Enhanced Callback Data Structure

The service sends enhanced callback data optimized for Laravel:

```json
{
  "task_id": "tempo_abc123",
  "status": "completed",
  "processing_type": "tempo",
  "started_at": "2025-08-16T10:30:00Z",
  "completed_at": "2025-08-16T10:30:45Z",
  "processing_time": 45.2,
  "original_analysis": {
    "bpm": 120.5,
    "key": "C major",
    "key_confidence": 0.85,
    "loudness_db": -12.3,
    "brightness": 0.72,
    "duration": 180.0
  },
  "tempo_processing": {
    "preset": "slowed_reverb",
    "tempo_factor": 0.75,
    "final_bpm": 90.4,
    "effects_applied": ["time_stretch", "pitch_shift", "reverb"]
  },
  "storage_paths": {
    "processed_audio": "processed/user_123/2025/08/16/song_tempo_slowed_reverb.wav",
    "stems_processed": { /* stem paths */ }
  },
  "public_urls": {
    "processed_audio": "https://storage.example.com/...",
    "stems_processed": { /* stem URLs */ }
  },
  "user_id": "123",
  "upload_id": "456",
  "project_id": "789",
  "cache_hit": false,
  "smart_suggestions": { /* AI suggestions */ },
  "metadata": { /* additional Laravel metadata */ }
}
```

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid tempo_factor: 5.0. Must be between 0.25 and 4.0",
  "error_code": "INVALID_PARAMETER"
}
```

#### 404 Not Found
```json
{
  "detail": "File not found in storage: uploads/user_123/nonexistent.mp3",
  "error_code": "FILE_NOT_FOUND"
}
```

#### 503 Service Unavailable
```json
{
  "detail": "Storage service is not enabled. Check storage configuration.",
  "error_code": "SERVICE_UNAVAILABLE"
}
```

#### Processing Errors (in callback)
```json
{
  "task_id": "tempo_abc123",
  "status": "failed",
  "error_message": "Audio file corrupted or unsupported format",
  "error_code": "PROCESSING_FAILED",
  "retry_count": 2
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Tempo Processing**: 3 requests per minute
- **Information Endpoints**: 60 requests per minute
- **Performance Endpoints**: 10 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 3
X-RateLimit-Remaining: 2
X-RateLimit-Reset: 1692188460
```

## Best Practices

### 1. Choose the Right Processing Mode

- **High Quality**: Use `use_stems=true` for best results
- **Fast Processing**: Use `use_stems=false` for quicker results
- **Custom Effects**: Use `preset="custom"` with specific parameters

### 2. Optimize for Your Use Case

```javascript
// For social media content (fast, viral effects)
{
  "preset": "sped_up",
  "use_stems": false  // Faster processing
}

// For professional remixes (high quality)
{
  "preset": "custom",
  "tempo_factor": 1.25,
  "pitch_shift_semitones": 2,
  "preserve_pitch": true,
  "use_stems": true  // Better quality
}

// For atmospheric content
{
  "preset": "slowed_reverb",
  "use_stems": true,  // Reverb sounds better on separated stems
  "add_reverb": true
}
```

### 3. Handle Callbacks Robustly

```php
// Always validate callback data
public function handleTempoCallback(Request $request)
{
    $validator = Validator::make($request->all(), [
        'task_id' => 'required|string',
        'status' => 'required|in:completed,failed,processing',
        'processing_type' => 'required|in:tempo'
    ]);
    
    if ($validator->fails()) {
        return response()->json(['error' => 'Invalid callback data'], 400);
    }
    
    // Process callback...
}
```

### 4. Monitor Performance

Regularly check performance metrics to optimize your usage:

```bash
# Check cache hit rate and processing times
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8001/tempo/performance/metrics"
```

## Examples

### Example 1: Simple Sped-Up Effect

```bash
curl -X POST "http://localhost:8001/tempo/process" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "audio_file=@original.mp3" \
  -F "preset=sped_up"
```

### Example 2: Custom Slowed + Reverb

```bash
curl -X POST "http://localhost:8001/tempo/storage/process" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "uploads/user_123/2025/08/16/song.mp3",
    "preset": "custom",
    "tempo_factor": 0.8,
    "pitch_shift_semitones": -1,
    "add_reverb": true,
    "use_stems": true,
    "callback_url": "https://myapp.com/api/callback"
  }'
```

### Example 3: High-Quality Nightcore

```bash
curl -X POST "http://localhost:8001/tempo/storage/process" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "uploads/user_123/2025/08/16/dance_track.mp3",
    "preset": "nightcore",
    "use_stems": true,
    "callback_url": "https://myapp.com/api/callback",
    "metadata": {
      "user_id": "123",
      "remix_type": "nightcore_high_quality"
    }
  }'
```

## Troubleshooting

### Common Issues

1. **Slow Processing Times**
   - Check if `use_stems=true` is necessary for your use case
   - Monitor cache hit rates - similar requests should be cached
   - Consider reducing audio file sizes

2. **Quality Issues**
   - Use `use_stems=true` for better quality
   - Avoid extreme `tempo_factor` values (stay within 0.5-2.0 for best results)
   - Check `processing_warnings` in the response for quality alerts

3. **Callback Issues**
   - Ensure callback URL is accessible from the audio service
   - Implement proper error handling in callback endpoints
   - Check callback delivery statistics via performance metrics

### Support

For additional support or custom integration requirements, contact the development team or check the service logs for detailed error information.