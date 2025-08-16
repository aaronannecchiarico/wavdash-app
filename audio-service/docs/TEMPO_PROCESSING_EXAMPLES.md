# Tempo Processing Examples & Use Cases

## Overview

This document provides practical examples and real-world use cases for the Tempo Processing API. These examples cover various scenarios from simple social media effects to professional remix creation.

## Quick Start Examples

### 1. Basic Sped-Up Effect (TikTok Style)

Perfect for creating viral social media content with the popular "chipmunk" effect.

**cURL:**
```bash
curl -X POST "http://localhost:8001/tempo/process" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "audio_file=@original_song.mp3" \
  -F "preset=sped_up" \
  -F "async_processing=true"
```

**Python:**
```python
import requests

url = "http://localhost:8001/tempo/process"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

files = {"audio_file": open("original_song.mp3", "rb")}
data = {
    "preset": "sped_up",
    "async_processing": True
}

response = requests.post(url, headers=headers, files=files, data=data)
task_id = response.json()["task_id"]
print(f"Processing started: {task_id}")
```

**JavaScript (Node.js):**
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('audio_file', fs.createReadStream('original_song.mp3'));
form.append('preset', 'sped_up');
form.append('async_processing', 'true');

axios.post('http://localhost:8001/tempo/process', form, {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    ...form.getHeaders()
  }
}).then(response => {
  console.log('Task ID:', response.data.task_id);
});
```

### 2. Atmospheric Slowed + Reverb

Creates the dreamy, atmospheric effect popular on Instagram and TikTok.

**Storage-Based Processing (Recommended):**
```bash
curl -X POST "http://localhost:8001/tempo/storage/process" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "uploads/user_123/2025/08/16/chill_track.mp3",
    "preset": "slowed_reverb",
    "use_stems": true,
    "callback_url": "https://myapp.com/api/tempo-callback"
  }'
```

**Expected Output:**
- Original BPM: 120 → Final BPM: ~90
- Pitch lowered by 2 semitones
- Atmospheric reverb added
- Individual stems processed for higher quality

## Advanced Use Cases

### 3. Professional Nightcore Remix

High-quality nightcore production with stem separation for professional results.

```python
import requests
import json

# Step 1: Upload to storage and get BPM analysis first
features_response = requests.post(
    "http://localhost:8001/storage/extract-features",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "storage_path": "uploads/user_456/2025/08/16/dance_track.wav",
        "callback_url": "https://myapp.com/api/features-callback"
    }
)

# Step 2: Use BPM data for intelligent tempo processing
def create_nightcore_remix(original_bpm, storage_path):
    # Calculate optimal tempo factor for nightcore
    target_bpm = 160  # Typical nightcore BPM
    tempo_factor = min(target_bpm / original_bpm, 2.0)  # Cap at 2x speed
    
    tempo_request = {
        "storage_path": storage_path,
        "preset": "custom",  # Custom for fine control
        "tempo_factor": tempo_factor,
        "pitch_shift_semitones": 4,  # Higher pitch for nightcore
        "preserve_pitch": False,
        "use_stems": True,  # High quality processing
        "add_reverb": False,  # Nightcore typically doesn't use reverb
        "callback_url": "https://myapp.com/api/nightcore-callback",
        "metadata": {
            "remix_type": "nightcore",
            "original_bpm": original_bpm,
            "target_bpm": target_bpm
        }
    }
    
    response = requests.post(
        "http://localhost:8001/tempo/storage/process",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
        json=tempo_request
    )
    
    return response.json()

# Usage
result = create_nightcore_remix(128, "uploads/user_456/2025/08/16/dance_track.wav")
print(f"Nightcore processing started: {result['task_id']}")
```

### 4. Custom Chopped & Screwed Style

Creating Houston-style chopped and screwed effects with custom parameters.

```javascript
// Custom chopped & screwed with additional processing
const choppedScrewedConfig = {
  storage_path: "uploads/user_789/2025/08/16/hip_hop_track.mp3",
  preset: "custom",
  tempo_factor: 0.6,        // Slow it down significantly
  pitch_shift_semitones: -4, // Lower pitch more than standard
  preserve_pitch: false,
  use_stems: true,
  callback_url: "https://myapp.com/api/chopped-callback",
  metadata: {
    style: "chopped_screwed",
    intensity: "heavy"
  }
};

fetch('http://localhost:8001/tempo/storage/process', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(choppedScrewedConfig)
})
.then(response => response.json())
.then(data => console.log('Chopped & Screwed processing:', data.task_id));
```

### 5. Batch Processing Multiple Presets

Process the same audio file with multiple different presets for A/B testing or providing options to users.

```python
import asyncio
import aiohttp

async def batch_tempo_processing(storage_path, presets):
    """Process the same audio with multiple presets simultaneously"""
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for preset_name in presets:
            task_data = {
                "storage_path": storage_path,
                "preset": preset_name,
                "use_stems": True,  # High quality for all
                "callback_url": f"https://myapp.com/api/tempo-callback/{preset_name}",
                "metadata": {
                    "preset_variant": preset_name,
                    "batch_id": "batch_001"
                }
            }
            
            task = session.post(
                "http://localhost:8001/tempo/storage/process",
                headers={"Authorization": "Bearer YOUR_API_KEY"},
                json=task_data
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        results = {}
        for i, response in enumerate(responses):
            data = await response.json()
            results[presets[i]] = data["task_id"]
        
        return results

# Usage
presets = ["sped_up", "slowed_reverb", "nightcore", "chopped_screwed"]
batch_results = await batch_tempo_processing(
    "uploads/user_999/2025/08/16/original.mp3", 
    presets
)

print("Batch processing started:")
for preset, task_id in batch_results.items():
    print(f"  {preset}: {task_id}")
```

## Laravel Integration Examples

### 6. Complete Laravel Workflow

Full integration showing file upload, processing, and result handling.

**Controller (ProcessTempoController.php):**
```php
<?php

namespace App\Http\Controllers;

use App\Models\AudioProcessing;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Validator;

class ProcessTempoController extends Controller
{
    public function processAudio(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'audio_file' => 'required|mimes:mp3,wav,flac|max:102400', // 100MB max
            'preset' => 'in:sped_up,slowed_reverb,nightcore,chopped_screwed,custom',
            'tempo_factor' => 'numeric|between:0.25,4.0',
            'high_quality' => 'boolean'
        ]);

        if ($validator->fails()) {
            return response()->json(['errors' => $validator->errors()], 400);
        }

        $user = auth()->user();
        $uploadedFile = $request->file('audio_file');
        
        // Store file in shared storage location
        $storagePath = Storage::putFile(
            "uploads/{$user->id}/" . date('Y/m/d'), 
            $uploadedFile
        );

        // Create processing record
        $processing = AudioProcessing::create([
            'user_id' => $user->id,
            'original_filename' => $uploadedFile->getClientOriginalName(),
            'storage_path' => $storagePath,
            'processing_type' => 'tempo',
            'status' => 'queued',
            'parameters' => [
                'preset' => $request->input('preset', 'slowed_reverb'),
                'tempo_factor' => $request->input('tempo_factor'),
                'high_quality' => $request->boolean('high_quality', false)
            ]
        ]);

        // Call audio processing service
        $serviceResponse = Http::timeout(30)->post(config('services.audio.url') . '/tempo/storage/process', [
            'storage_path' => $storagePath,
            'preset' => $request->input('preset', 'slowed_reverb'),
            'tempo_factor' => $request->input('tempo_factor'),
            'use_stems' => $request->boolean('high_quality', false),
            'callback_url' => route('api.tempo.callback'),
            'metadata' => [
                'user_id' => $user->id,
                'processing_id' => $processing->id,
                'upload_id' => $processing->id
            ]
        ]);

        if ($serviceResponse->successful()) {
            $taskId = $serviceResponse->json('task_id');
            $processing->update(['task_id' => $taskId, 'status' => 'processing']);

            return response()->json([
                'processing_id' => $processing->id,
                'task_id' => $taskId,
                'status' => 'processing',
                'message' => 'Your audio is being processed! You\'ll receive a notification when it\'s ready.',
                'estimated_completion' => now()->addMinutes(2)->toISOString()
            ]);
        } else {
            $processing->update(['status' => 'failed', 'error_message' => 'Service unavailable']);
            return response()->json(['error' => 'Audio processing service unavailable'], 503);
        }
    }

    public function handleCallback(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'task_id' => 'required|string',
            'status' => 'required|in:completed,failed,processing',
            'metadata.processing_id' => 'required|integer'
        ]);

        if ($validator->fails()) {
            \Log::warning('Invalid tempo callback received', $request->all());
            return response()->json(['error' => 'Invalid callback data'], 400);
        }

        $processingId = $request->input('metadata.processing_id');
        $processing = AudioProcessing::find($processingId);

        if (!$processing) {
            \Log::error('Processing record not found', ['id' => $processingId]);
            return response()->json(['error' => 'Processing record not found'], 404);
        }

        // Update processing record
        $processing->update([
            'status' => $request->input('status'),
            'result_data' => $request->all(),
            'completed_at' => $request->input('status') === 'completed' ? now() : null,
            'error_message' => $request->input('error_message')
        ]);

        if ($request->input('status') === 'completed') {
            // Create download URLs and notify user
            $this->handleSuccessfulProcessing($processing, $request->all());
        } elseif ($request->input('status') === 'failed') {
            // Handle failure
            $this->handleFailedProcessing($processing, $request->input('error_message'));
        }

        return response()->json(['status' => 'received']);
    }

    private function handleSuccessfulProcessing(AudioProcessing $processing, array $callbackData)
    {
        // Store result URLs
        $outputFiles = $callbackData['output_files'] ?? [];
        $publicUrls = $callbackData['public_urls'] ?? [];
        
        $processing->update([
            'output_files' => $outputFiles,
            'public_urls' => $publicUrls,
            'processing_metadata' => [
                'original_analysis' => $callbackData['original_analysis'] ?? [],
                'tempo_processing' => $callbackData['tempo_processing'] ?? [],
                'processing_time' => $callbackData['processing_time'] ?? 0
            ]
        ]);

        // Send notification to user
        $processing->user->notify(new AudioProcessingCompleted($processing));

        // Trigger any additional workflows (e.g., social media posting)
        dispatch(new PostToSocialMediaJob($processing));
    }

    private function handleFailedProcessing(AudioProcessing $processing, string $errorMessage)
    {
        \Log::error('Audio processing failed', [
            'processing_id' => $processing->id,
            'error' => $errorMessage
        ]);

        // Notify user of failure
        $processing->user->notify(new AudioProcessingFailed($processing, $errorMessage));
    }

    public function getProcessingStatus($processingId)
    {
        $processing = AudioProcessing::where('user_id', auth()->id())
            ->findOrFail($processingId);

        return response()->json([
            'id' => $processing->id,
            'status' => $processing->status,
            'progress' => $this->calculateProgress($processing),
            'result_data' => $processing->result_data,
            'output_files' => $processing->output_files,
            'public_urls' => $processing->public_urls,
            'created_at' => $processing->created_at,
            'completed_at' => $processing->completed_at
        ]);
    }

    private function calculateProgress(AudioProcessing $processing): int
    {
        switch ($processing->status) {
            case 'queued': return 10;
            case 'processing': return 50;
            case 'completed': return 100;
            case 'failed': return 0;
            default: return 0;
        }
    }
}
```

**Model (AudioProcessing.php):**
```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class AudioProcessing extends Model
{
    protected $fillable = [
        'user_id',
        'task_id',
        'original_filename',
        'storage_path',
        'processing_type',
        'status',
        'parameters',
        'result_data',
        'output_files',
        'public_urls',
        'processing_metadata',
        'error_message',
        'completed_at'
    ];

    protected $casts = [
        'parameters' => 'json',
        'result_data' => 'json',
        'output_files' => 'json',
        'public_urls' => 'json',
        'processing_metadata' => 'json',
        'completed_at' => 'datetime'
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function getDownloadUrlAttribute(): ?string
    {
        return $this->public_urls['processed_audio'] ?? null;
    }

    public function getStemDownloadUrlsAttribute(): array
    {
        return $this->public_urls['stems_processed'] ?? [];
    }

    public function isCompleted(): bool
    {
        return $this->status === 'completed';
    }

    public function isFailed(): bool
    {
        return $this->status === 'failed';
    }

    public function getProcessingTimeAttribute(): ?float
    {
        return $this->processing_metadata['processing_time'] ?? null;
    }

    public function getOriginalBpmAttribute(): ?float
    {
        return $this->processing_metadata['original_analysis']['bpm'] ?? null;
    }

    public function getFinalBpmAttribute(): ?float
    {
        return $this->processing_metadata['tempo_processing']['final_bpm'] ?? null;
    }
}
```

### 7. Frontend Integration (Vue.js)

Complete frontend component for tempo processing.

**TempoProcessor.vue:**
```vue
<template>
  <div class="tempo-processor">
    <div class="upload-section" v-if="!processing">
      <input 
        type="file" 
        @change="handleFileSelect"
        accept="audio/*"
        ref="fileInput"
        class="file-input"
      />
      
      <div class="preset-selection">
        <h3>Choose a Style:</h3>
        <div class="preset-grid">
          <div 
            v-for="preset in availablePresets" 
            :key="preset.key"
            :class="['preset-card', { active: selectedPreset === preset.key }]"
            @click="selectedPreset = preset.key"
          >
            <h4>{{ preset.name }}</h4>
            <p>{{ preset.description }}</p>
            <div class="preset-preview">
              <span>Tempo: {{ (preset.tempo_factor * 100).toFixed(0) }}%</span>
              <span>Pitch: {{ preset.pitch_shift_semitones > 0 ? '+' : '' }}{{ preset.pitch_shift_semitones }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="quality-options">
        <label>
          <input type="checkbox" v-model="highQuality" />
          High Quality Processing (slower, better results)
        </label>
      </div>

      <button 
        @click="processAudio" 
        :disabled="!selectedFile"
        class="process-button"
      >
        Create {{ getPresetName(selectedPreset) }} Version
      </button>
    </div>

    <div class="processing-section" v-if="processing">
      <div class="progress-indicator">
        <div class="spinner"></div>
        <h3>Creating your {{ getPresetName(selectedPreset) }} version...</h3>
        <p>{{ processingMessage }}</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
      </div>
    </div>

    <div class="results-section" v-if="completed">
      <h3>Your {{ getPresetName(selectedPreset) }} version is ready!</h3>
      
      <div class="audio-comparison">
        <div class="audio-player">
          <h4>Original</h4>
          <audio controls :src="originalFileUrl" preload="metadata"></audio>
          <div class="audio-info">
            <span>BPM: {{ originalBpm }}</span>
          </div>
        </div>
        
        <div class="audio-player">
          <h4>{{ getPresetName(selectedPreset) }} Version</h4>
          <audio controls :src="processedFileUrl" preload="metadata"></audio>
          <div class="audio-info">
            <span>BPM: {{ finalBpm }}</span>
            <span>Processing time: {{ processingTime }}s</span>
          </div>
        </div>
      </div>

      <div class="download-section">
        <a :href="processedFileUrl" download class="download-button">
          Download Processed Audio
        </a>
        
        <div v-if="stemUrls.length > 0" class="stems-download">
          <h4>Individual Stems:</h4>
          <div class="stem-downloads">
            <a 
              v-for="(url, stemName) in stemUrls" 
              :key="stemName"
              :href="url" 
              download 
              class="stem-download-button"
            >
              {{ stemName.charAt(0).toUpperCase() + stemName.slice(1) }}
            </a>
          </div>
        </div>
      </div>

      <button @click="reset" class="reset-button">
        Process Another File
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TempoProcessor',
  data() {
    return {
      selectedFile: null,
      selectedPreset: 'slowed_reverb',
      highQuality: false,
      processing: false,
      completed: false,
      progress: 0,
      processingMessage: 'Uploading file...',
      processingId: null,
      originalFileUrl: null,
      processedFileUrl: null,
      originalBpm: null,
      finalBpm: null,
      processingTime: null,
      stemUrls: {},
      availablePresets: [
        {
          key: 'sped_up',
          name: 'Sped Up',
          description: 'Popular chipmunk effect - faster tempo with higher pitch',
          tempo_factor: 1.25,
          pitch_shift_semitones: 3
        },
        {
          key: 'slowed_reverb',
          name: 'Slowed + Reverb',
          description: 'Dreamy slowed-down effect with atmospheric reverb',
          tempo_factor: 0.75,
          pitch_shift_semitones: -2
        },
        {
          key: 'nightcore',
          name: 'Nightcore',
          description: 'Fast tempo with high pitch and enhanced brightness',
          tempo_factor: 1.4,
          pitch_shift_semitones: 4
        },
        {
          key: 'chopped_screwed',
          name: 'Chopped & Screwed',
          description: 'Houston-style slow tempo with low-pass filtering',
          tempo_factor: 0.6,
          pitch_shift_semitones: -3
        }
      ]
    }
  },
  methods: {
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
      if (this.selectedFile) {
        this.originalFileUrl = URL.createObjectURL(this.selectedFile);
      }
    },
    
    async processAudio() {
      if (!this.selectedFile) return;
      
      this.processing = true;
      this.progress = 10;
      
      try {
        const formData = new FormData();
        formData.append('audio_file', this.selectedFile);
        formData.append('preset', this.selectedPreset);
        formData.append('high_quality', this.highQuality);
        
        const response = await fetch('/api/tempo/process', {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Bearer ${this.$auth.token()}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Upload failed');
        }
        
        const data = await response.json();
        this.processingId = data.processing_id;
        this.progress = 30;
        this.processingMessage = 'Processing audio with tempo effects...';
        
        // Poll for completion
        this.pollProcessingStatus();
        
      } catch (error) {
        console.error('Processing failed:', error);
        this.processing = false;
        this.$toast.error('Failed to process audio. Please try again.');
      }
    },
    
    async pollProcessingStatus() {
      try {
        const response = await fetch(`/api/tempo/status/${this.processingId}`, {
          headers: {
            'Authorization': `Bearer ${this.$auth.token()}`
          }
        });
        
        const data = await response.json();
        
        this.progress = data.progress;
        
        if (data.status === 'completed') {
          this.handleProcessingComplete(data);
        } else if (data.status === 'failed') {
          throw new Error(data.error_message || 'Processing failed');
        } else {
          // Continue polling
          setTimeout(() => this.pollProcessingStatus(), 2000);
        }
        
      } catch (error) {
        console.error('Status check failed:', error);
        this.processing = false;
        this.$toast.error('Processing failed. Please try again.');
      }
    },
    
    handleProcessingComplete(data) {
      this.processing = false;
      this.completed = true;
      this.processedFileUrl = data.download_url;
      this.stemUrls = data.stem_download_urls || {};
      this.originalBpm = data.original_bpm;
      this.finalBpm = data.final_bpm;
      this.processingTime = data.processing_time;
      
      this.$toast.success(`Your ${this.getPresetName(this.selectedPreset)} version is ready!`);
    },
    
    getPresetName(presetKey) {
      const preset = this.availablePresets.find(p => p.key === presetKey);
      return preset ? preset.name : 'Custom';
    },
    
    reset() {
      this.selectedFile = null;
      this.processing = false;
      this.completed = false;
      this.progress = 0;
      this.processingId = null;
      this.originalFileUrl = null;
      this.processedFileUrl = null;
      this.stemUrls = {};
      this.$refs.fileInput.value = '';
    }
  }
}
</script>

<style scoped>
.tempo-processor {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.preset-card {
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.preset-card:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0,123,255,0.2);
}

.preset-card.active {
  border-color: #007bff;
  background-color: #f8f9fa;
}

.preset-preview {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 0.9em;
  color: #6c757d;
}

.progress-indicator {
  text-align: center;
  padding: 40px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 15px;
}

.progress-fill {
  height: 100%;
  background-color: #007bff;
  transition: width 0.3s ease;
}

.audio-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 20px 0;
}

.audio-player {
  padding: 15px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
}

.audio-info {
  margin-top: 10px;
  font-size: 0.9em;
  color: #6c757d;
}

.audio-info span {
  margin-right: 15px;
}

.download-section {
  text-align: center;
  margin: 30px 0;
}

.download-button {
  background-color: #28a745;
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  text-decoration: none;
  display: inline-block;
  margin-bottom: 20px;
}

.stem-downloads {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.stem-download-button {
  background-color: #6c757d;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.9em;
}

.process-button, .reset-button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  margin: 10px;
}

.process-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.reset-button {
  background-color: #6c757d;
}
</style>
```

## Performance Optimization Examples

### 8. Smart Caching Strategy

Implementing intelligent caching for better performance.

```python
import hashlib
import requests
from typing import Dict, Any

class TempoProcessingClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash of audio file for caching"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_processing_key(self, file_hash: str, params: Dict[str, Any]) -> str:
        """Generate unique key for processing parameters"""
        param_str = str(sorted(params.items()))
        return hashlib.md5(f"{file_hash}_{param_str}".encode()).hexdigest()
    
    def process_with_cache(self, storage_path: str, **params) -> Dict[str, Any]:
        """Process audio with intelligent caching"""
        
        # Check if we've processed this exact combination before
        file_hash = self._get_file_hash(storage_path)
        processing_key = self._get_processing_key(file_hash, params)
        
        # Check local cache first
        cached_result = self._check_local_cache(processing_key)
        if cached_result:
            print(f"🚀 Cache hit! Using cached result for {processing_key[:8]}...")
            return cached_result
        
        # Process with service
        response = self.session.post(
            f"{self.base_url}/tempo/storage/process",
            json={
                "storage_path": storage_path,
                **params,
                "callback_url": f"https://myapp.com/api/cache-callback/{processing_key}"
            }
        )
        
        return response.json()
```

### 9. Monitoring and Analytics

Implementing comprehensive monitoring for tempo processing operations.

```python
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

@dataclass
class ProcessingMetrics:
    preset: str
    processing_time: float
    file_size_mb: float
    cache_hit: bool
    quality_score: float
    user_satisfaction: int  # 1-5 rating
    timestamp: datetime

class TempoProcessingAnalytics:
    def __init__(self):
        self.metrics: List[ProcessingMetrics] = []
        self.logger = logging.getLogger(__name__)
    
    def record_processing(self, metrics: ProcessingMetrics):
        """Record processing metrics for analysis"""
        self.metrics.append(metrics)
        
        # Log key insights
        if metrics.cache_hit:
            self.logger.info(f"🚀 Cache hit for {metrics.preset} preset (saved {metrics.processing_time:.1f}s)")
        
        if metrics.processing_time > 60:
            self.logger.warning(f"⚠️ Slow processing: {metrics.processing_time:.1f}s for {metrics.preset}")
    
    def get_performance_insights(self, days: int = 7) -> Dict[str, Any]:
        """Generate performance insights for the last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {"message": "No recent data available"}
        
        # Calculate insights
        total_requests = len(recent_metrics)
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        avg_processing_time = sum(m.processing_time for m in recent_metrics) / total_requests
        
        # Preset popularity
        preset_usage = {}
        for m in recent_metrics:
            preset_usage[m.preset] = preset_usage.get(m.preset, 0) + 1
        
        # Quality analysis
        avg_quality = sum(m.quality_score for m in recent_metrics) / total_requests
        avg_satisfaction = sum(m.user_satisfaction for m in recent_metrics if m.user_satisfaction > 0)
        satisfaction_responses = sum(1 for m in recent_metrics if m.user_satisfaction > 0)
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "cache_hit_rate": (cache_hits / total_requests) * 100,
            "average_processing_time": round(avg_processing_time, 2),
            "preset_popularity": dict(sorted(preset_usage.items(), key=lambda x: x[1], reverse=True)),
            "quality_metrics": {
                "average_quality_score": round(avg_quality, 2),
                "average_user_satisfaction": round(avg_satisfaction / satisfaction_responses, 2) if satisfaction_responses > 0 else None,
                "satisfaction_response_rate": (satisfaction_responses / total_requests) * 100
            },
            "recommendations": self._generate_recommendations(recent_metrics)
        }
    
    def _generate_recommendations(self, metrics: List[ProcessingMetrics]) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        cache_hit_rate = sum(1 for m in metrics if m.cache_hit) / len(metrics)
        avg_processing_time = sum(m.processing_time for m in metrics) / len(metrics)
        
        if cache_hit_rate < 0.3:
            recommendations.append("Consider implementing more aggressive caching - cache hit rate is low")
        
        if avg_processing_time > 30:
            recommendations.append("Average processing time is high - consider optimizing default settings")
        
        # Check for popular presets
        preset_counts = {}
        for m in metrics:
            preset_counts[m.preset] = preset_counts.get(m.preset, 0) + 1
        
        most_popular = max(preset_counts.items(), key=lambda x: x[1])
        if most_popular[1] > len(metrics) * 0.5:
            recommendations.append(f"'{most_popular[0]}' preset is very popular - consider creating variations")
        
        return recommendations

# Usage example
analytics = TempoProcessingAnalytics()

# Record processing results
analytics.record_processing(ProcessingMetrics(
    preset="slowed_reverb",
    processing_time=25.3,
    file_size_mb=12.5,
    cache_hit=False,
    quality_score=8.7,
    user_satisfaction=4,
    timestamp=datetime.now()
))

# Get insights
insights = analytics.get_performance_insights(days=30)
print(f"Cache hit rate: {insights['cache_hit_rate']:.1f}%")
print(f"Most popular preset: {list(insights['preset_popularity'].keys())[0]}")
```

## Troubleshooting Examples

### 10. Error Handling and Recovery

Comprehensive error handling for various failure scenarios.

```python
import requests
import time
import logging
from typing import Optional, Dict, Any

class RobustTempoProcessor:
    def __init__(self, api_key: str, base_url: str, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
    
    def process_with_retry(self, storage_path: str, **params) -> Optional[Dict[str, Any]]:
        """Process audio with automatic retry and error handling"""
        
        for attempt in range(self.max_retries + 1):
            try:
                result = self._attempt_processing(storage_path, attempt, **params)
                if result:
                    return result
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries:
                    self._wait_before_retry(attempt)
                    
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error on attempt {attempt + 1}")
                if attempt < self.max_retries:
                    self._wait_before_retry(attempt)
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    self.logger.warning("Rate limited, waiting longer...")
                    time.sleep(60)  # Wait 1 minute for rate limit reset
                elif e.response.status_code >= 500:  # Server error
                    self.logger.warning(f"Server error {e.response.status_code} on attempt {attempt + 1}")
                    if attempt < self.max_retries:
                        self._wait_before_retry(attempt)
                else:
                    # Client error - don't retry
                    self.logger.error(f"Client error {e.response.status_code}: {e.response.text}")
                    return None
                    
        self.logger.error("All retry attempts failed")
        return None
    
    def _attempt_processing(self, storage_path: str, attempt: int, **params) -> Optional[Dict[str, Any]]:
        """Single processing attempt with error handling"""
        
        # Adjust parameters based on attempt number for better success rate
        adjusted_params = self._adjust_params_for_retry(params, attempt)
        
        response = requests.post(
            f"{self.base_url}/tempo/storage/process",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "storage_path": storage_path,
                **adjusted_params
            },
            timeout=30
        )
        
        response.raise_for_status()
        
        result = response.json()
        task_id = result.get("task_id")
        
        if not task_id:
            self.logger.error("No task ID received")
            return None
        
        # Wait for completion with timeout
        return self._wait_for_completion(task_id, timeout_minutes=10)
    
    def _adjust_params_for_retry(self, params: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Adjust processing parameters for retry attempts"""
        adjusted = params.copy()
        
        if attempt > 0:
            # Reduce quality for faster processing on retries
            adjusted["use_stems"] = False
            self.logger.info(f"Retry {attempt}: Using fast processing mode")
        
        if attempt > 1:
            # Use more conservative tempo settings
            if "tempo_factor" in adjusted:
                factor = adjusted["tempo_factor"]
                if factor < 1.0:
                    adjusted["tempo_factor"] = max(factor, 0.75)  # Not too slow
                elif factor > 1.0:
                    adjusted["tempo_factor"] = min(factor, 1.5)   # Not too fast
                self.logger.info(f"Retry {attempt}: Using conservative tempo factor {adjusted['tempo_factor']}")
        
        return adjusted
    
    def _wait_before_retry(self, attempt: int):
        """Exponential backoff with jitter"""
        wait_time = min(2 ** attempt + random.uniform(0, 1), 30)  # Cap at 30 seconds
        self.logger.info(f"Waiting {wait_time:.1f}s before retry...")
        time.sleep(wait_time)
    
    def _wait_for_completion(self, task_id: str, timeout_minutes: int = 10) -> Optional[Dict[str, Any]]:
        """Wait for processing completion with timeout"""
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                # Check task status (this would be your status endpoint)
                status_response = requests.get(
                    f"{self.base_url}/tasks/{task_id}/status",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10
                )
                
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if status_data.get("status") == "completed":
                    return status_data
                elif status_data.get("status") == "failed":
                    self.logger.error(f"Processing failed: {status_data.get('error_message')}")
                    return None
                
                # Still processing, wait a bit
                time.sleep(5)
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Status check failed: {e}")
                time.sleep(10)  # Wait longer on status check failure
        
        self.logger.error(f"Processing timeout after {timeout_minutes} minutes")
        return None

# Usage
processor = RobustTempoProcessor("YOUR_API_KEY", "http://localhost:8001")

result = processor.process_with_retry(
    "uploads/user_123/2025/08/16/song.mp3",
    preset="slowed_reverb",
    use_stems=True
)

if result:
    print("Processing completed successfully!")
    print(f"Download URL: {result.get('download_url')}")
else:
    print("Processing failed after all retry attempts")
```

This comprehensive collection of examples covers the full spectrum of tempo processing use cases, from simple social media effects to complex professional workflows. Each example includes practical implementation details and can be adapted to specific requirements.