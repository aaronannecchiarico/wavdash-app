# Sped-Up and Slowed-Down Audio Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to implement sped-up and slowed-down audio processing capabilities into the existing Beat Forge Audio Feature Extraction Service. The implementation leverages both existing stem separation and feature extraction capabilities alongside Spotify's Pedalboard library to create popular social media audio effects.

## Background & Requirements

### Popular Social Media Trends
- **Sped-up versions**: Chipmunk effect (tempo + pitch increase)
- **Slowed + Reverb**: Dreamy, atmospheric effect popular on TikTok
- **Nightcore style**: Fast tempo with higher pitch and brightness
- **Chopped and Screwed**: Slow tempo with lower pitch and filtering
- **Time-stretched**: Tempo changes while preserving original pitch

### Technical Requirements
- Integrate with existing FastAPI/Celery architecture
- Support both direct upload and storage-based processing (Laravel integration)
- Leverage existing BPM detection and stem separation capabilities
- Maintain user-based folder structure and callback patterns
- Apple Silicon compatibility (CPU processing)

## Architecture Overview

### Processing Pipeline
```
Audio Input → [Feature Extraction] → [Optional Stem Separation] → [Tempo/Pitch Processing] → Output
                     ↓                        ↓                           ↓
                BPM, Key, etc.          Vocals, Drums,              Pedalboard Effects
                                       Bass, Other                  + Time Stretching
```

### Integration Points
1. **Existing Feature Extraction**: Use detected BPM for intelligent tempo processing
2. **Existing Stem Separation**: Process stems individually for higher quality results
3. **Existing Storage**: Follow established patterns for file organization and callbacks
4. **Existing Task Processing**: Add new Celery tasks following current conventions

## API Design

### New Endpoints

#### Direct File Upload
```
POST /process-tempo
POST /process-tempo-sync
```

#### Storage-Based Processing (Recommended for Laravel)
```
POST /storage/process-tempo
```

### Request Parameters
```json
{
  "storage_path": "uploads/user_id/2025/08/13/filename.mp3",
  "preset": "slowed_reverb",  // or "sped_up", "nightcore", "chopped_screwed", "custom"
  "tempo_factor": 0.75,       // 0.25-4.0 range
  "pitch_shift_semitones": -2, // -12 to +12 range
  "preserve_pitch": false,     // true = time stretch only
  "add_reverb": true,
  "use_stems": true,          // process stems separately for quality
  "callback_url": "https://yourapp.com/api/callback",
  "metadata": {
    "user_id": "1",
    "upload_id": "123"
  }
}
```

### Response Format
```json
{
  "task_id": "abc123-def456",
  "status": "completed",
  "original_analysis": {
    "bpm": 120.5,
    "key": "C major",
    "duration": 180.0
  },
  "tempo_processing": {
    "preset": "slowed_reverb",
    "tempo_factor": 0.75,
    "pitch_shift_semitones": -2,
    "final_bpm": 90.4,
    "processing_method": "stems_separate",
    "effects_applied": ["time_stretch", "pitch_shift", "reverb"]
  },
  "output_files": {
    "processed_audio": "processed/user_id/2025/08/13/filename_tempo_slowed_reverb.wav",
    "stems_processed": {
      "vocals": "processed/user_id/2025/08/13/filename_vocals_slowed_reverb.wav",
      "drums": "processed/user_id/2025/08/13/filename_drums_slowed_reverb.wav",
      "bass": "processed/user_id/2025/08/13/filename_bass_slowed_reverb.wav",
      "other": "processed/user_id/2025/08/13/filename_other_slowed_reverb.wav"
    }
  },
  "public_urls": {
    "processed_audio": "https://storage.url/...",
    "stems_processed": { /* URLs for each stem */ }
  },
  "processing_time": 45.2
}
```

## Technical Implementation

### Dependencies
```python
# requirements.txt additions
pedalboard>=0.7.0
soundfile>=0.10.0  # Enhanced audio I/O support
```

### Core Processing Logic

#### 1. Preset Definitions
```python
TEMPO_PRESETS = {
    "sped_up": {
        "tempo_factor": 1.25,
        "pitch_shift_semitones": 3,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "brightness_boost"]
    },
    "slowed_reverb": {
        "tempo_factor": 0.75,
        "pitch_shift_semitones": -2,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "reverb"],
        "reverb_settings": {"wet_level": 0.3, "room_size": 0.4}
    },
    "nightcore": {
        "tempo_factor": 1.4,
        "pitch_shift_semitones": 4,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "brightness_boost", "compression"]
    },
    "chopped_screwed": {
        "tempo_factor": 0.6,
        "pitch_shift_semitones": -3,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "low_pass_filter"]
    }
}
```

#### 2. Pedalboard Processing Chains
```python
def create_processing_board(preset_name: str, custom_params: dict = None):
    preset = TEMPO_PRESETS[preset_name]
    effects = []
    
    if "pitch_shift" in preset["effects"]:
        effects.append(PitchShift(semitones=preset["pitch_shift_semitones"]))
    
    if "reverb" in preset["effects"]:
        reverb_settings = preset.get("reverb_settings", {})
        effects.append(Reverb(
            wet_level=reverb_settings.get("wet_level", 0.25),
            room_size=reverb_settings.get("room_size", 0.3)
        ))
    
    if "brightness_boost" in preset["effects"]:
        effects.append(HighShelfFilter(cutoff_hz=3000, gain_db=2))
    
    return Pedalboard(effects)
```

#### 3. Hybrid Processing Approach
```python
def process_audio_with_tempo(audio_data, sample_rate, tempo_factor, preserve_pitch, pedalboard_effects):
    """
    Combines librosa time stretching with pedalboard effects processing
    """
    # Step 1: Handle tempo changes
    if preserve_pitch and tempo_factor != 1.0:
        # Use librosa for high-quality time stretching
        audio_data = librosa.effects.time_stretch(audio_data, rate=tempo_factor)
    elif tempo_factor != 1.0 and not preserve_pitch:
        # Traditional speed change (affects both tempo and pitch)
        indices = np.round(np.arange(0, len(audio_data), tempo_factor)).astype(int)
        audio_data = audio_data[indices[indices < len(audio_data)]]
    
    # Step 2: Apply pedalboard effects (pitch shift, reverb, etc.)
    if pedalboard_effects:
        audio_data = pedalboard_effects(audio_data, sample_rate)
    
    return audio_data
```

#### 4. Stems-Based Processing
```python
def process_stems_individually(stems_paths, preset, user_id):
    """
    Process each stem with optimized settings for stem type
    """
    processed_stems = {}
    
    for stem_name, stem_path in stems_paths.items():
        # Load stem audio
        with AudioFile(stem_path) as f:
            audio = f.read(f.frames)
        
        # Create stem-specific processing board
        if stem_name == 'vocals':
            # More conservative pitch processing for vocals
            board = create_vocal_processing_board(preset)
        elif stem_name == 'drums':
            # Preserve transients, focus on time stretching
            board = create_drum_processing_board(preset)
        else:
            # Standard processing for bass/other
            board = create_standard_processing_board(preset)
        
        # Process and save
        processed_audio = process_audio_with_tempo(
            audio, f.samplerate, 
            preset["tempo_factor"], 
            preset.get("preserve_pitch", False),
            board
        )
        
        # Save processed stem
        output_path = generate_stem_output_path(stem_path, preset["name"], user_id)
        save_audio_file(processed_audio, f.samplerate, output_path)
        processed_stems[stem_name] = output_path
    
    return processed_stems
```

### File Organization
Following existing patterns:
```
processed/{user_id}/YYYY/MM/DD/filename_tempo_{preset}.wav
processed/{user_id}/YYYY/MM/DD/filename_tempo_{preset}_metadata.json
processed/{user_id}/YYYY/MM/DD/filename_{stem}_tempo_{preset}.wav  # for individual stems
```

### Celery Task Structure
```python
@celery_app.task(bind=True, name='tasks.tempo_processing.process_tempo_from_storage', queue='tempo_processing')
def process_tempo_from_storage(
    self, 
    task_id: str, 
    storage_path: str,
    preset: str = "custom",
    tempo_factor: float = 1.0,
    pitch_shift_semitones: float = 0.0,
    preserve_pitch: bool = False,
    use_stems: bool = False,
    callback_url: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    # Implementation following existing patterns in storage_processing.py
    pass
```

## Performance & Rate Limiting

### Processing Time Estimates
- **Full mix processing**: 30-60 seconds for 3-4 minute song
- **Stems-based processing**: 2-4x longer but significantly better quality
- **Simple presets**: Faster than complex multi-effect chains

### Rate Limiting Strategy
- **Tempo processing**: 3 requests/minute (due to complexity)
- **Fast mode** (full mix): 5 requests/minute  
- **Quality mode** (stems-based): 2 requests/minute

### Queue Management
- New queue: `tempo_processing`
- Pipeline dependencies: `audio_features` → `stem_separation` (if needed) → `tempo_processing`

## Integration with Existing Features

### BPM-Aware Processing
```python
def calculate_optimal_tempo_factor(current_bpm: float, target_style: str):
    """
    Use detected BPM to suggest optimal tempo factors for different styles
    """
    BPM_TARGETS = {
        "chill": (70, 90),
        "pop": (100, 130),
        "dance": (120, 140),
        "hyper": (140, 180)
    }
    
    if target_style in BPM_TARGETS:
        min_bpm, max_bpm = BPM_TARGETS[target_style]
        target_bpm = (min_bpm + max_bpm) / 2
        return target_bpm / current_bpm
    
    return 1.0
```

### Callback Integration
Extend existing `StorageCallbackData` model:
```python
@dataclass
class TempoProcessingCallbackData(StorageCallbackData):
    tempo_processing_data: Optional[Dict[str, Any]] = None
    original_analysis: Optional[Dict[str, Any]] = None
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Add pedalboard and dependencies to requirements.txt
- [ ] Create new Pydantic models (`models/tempo_models.py`)
- [ ] Add basic API endpoints (`routes/tempo_processing.py`)
- [ ] Implement core tempo processing task (full mix only)
- [ ] Basic preset system
- [ ] Unit tests for core functionality

### Phase 2: Advanced Features (Week 3-4)
- [ ] Integrate with existing stem separation workflow
- [ ] Implement stems-based processing for higher quality
- [ ] Add all popular presets with proper effect chains
- [ ] BPM-aware processing suggestions
- [ ] Enhanced error handling and validation
- [ ] Feature tests with real audio files

### Phase 3: Optimization & Polish (Week 5-6)
- [ ] Performance optimization and caching strategies
- [ ] Enhanced callback integration for Laravel
- [ ] Comprehensive documentation and API examples
- [ ] Load testing and rate limit tuning
- [ ] Production deployment preparation

## Testing Strategy

### Unit Tests
- Tempo processing functions
- Preset configuration validation
- Audio quality metrics
- Error handling scenarios

### Feature Tests
- End-to-end processing with real audio files
- Integration with existing stem separation
- Storage upload/download workflows
- Callback functionality

### Performance Tests
- Processing time benchmarks
- Memory usage monitoring
- Concurrent request handling
- Rate limiting effectiveness

## Error Handling & Validation

### Input Validation
- Tempo factor range: 0.25x to 4.0x
- Pitch shift range: -12 to +12 semitones
- File size and duration limits
- Audio format compatibility

### Error Scenarios
- Missing dependencies (graceful degradation)
- Processing failures (proper cleanup)
- Storage integration failures
- Quality degradation warnings for extreme settings

### Monitoring
- Processing success/failure rates
- Average processing times by preset
- Popular preset usage statistics
- Quality metrics and user feedback

## Dependencies & Requirements

### New Python Dependencies
```
pedalboard>=0.7.0
soundfile>=0.10.0
librosa>=0.9.0  # Enhanced for time stretching
```

### System Requirements
- Same as existing system (CPU processing for Apple Silicon compatibility)
- Additional disk space for temporary processing files
- Increased memory usage during stems-based processing

## Conclusion

This implementation plan provides a comprehensive approach to adding popular sped-up and slowed-down audio effects to the existing service. By leveraging both the current stem separation and feature extraction capabilities alongside Pedalboard's powerful effects processing, the service can offer high-quality tempo and pitch processing that meets the demands of social media content creators.

The phased approach ensures gradual implementation with continuous testing and optimization, while maintaining full compatibility with the existing Laravel integration and storage architecture.