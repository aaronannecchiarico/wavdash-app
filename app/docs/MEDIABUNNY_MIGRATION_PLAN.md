# MediaBunny Client-Side Audio Processing Migration Plan

## Executive Summary

This document outlines a plan to migrate Beat Forge's server-side audio processing pipeline to client-side processing using the MediaBunny library. This migration will significantly reduce server load, eliminate processing delays, and reduce hosting costs while maintaining full compatibility with existing storage systems.

**Recommendation: PROCEED with migration**

## Current State Analysis

### Current Audio Processing Pipeline
1. **Upload**: Users upload audio files via React form component
2. **Storage**: Files stored on Cloudflare R2 (primary) or local storage (fallback)
3. **Queue Processing**: `ProcessAudioUpload` Laravel job handles conversion
4. **Server Processing**: FFmpeg converts files to OGG Vorbis (128kbps, stereo)
5. **Storage Update**: Processed files uploaded back to storage
6. **WebSocket Notification**: Users notified via Laravel Reverb when complete

### Current Infrastructure Costs
- **CPU-intensive FFmpeg processing** on Laravel servers
- **Memory usage** for temporary file handling
- **Storage overhead** for temp files during processing
- **Queue worker resources** for background job processing
- **Bandwidth costs** for R2 → Server → R2 file transfers

## MediaBunny Library Assessment

### Capabilities
- **Zero-dependency** JavaScript library built in TypeScript
- **25+ codec support** including MP3, OGG, AAC, WebM, WAV
- **Hardware acceleration** via WebCodecs API
- **Precise control** over bitrate, sample rate, channel configuration
- **Streaming I/O** support for large files
- **Browser compatibility** with fallback mechanisms

### Compatibility with Beat Forge
- ✅ **OGG Vorbis output**: Fully supported with precise bitrate control
- ✅ **Storage integration**: Compatible with existing R2 and local storage
- ✅ **File size handling**: Optimized for large audio files
- ✅ **Progress tracking**: Real-time client-side progress feedback
- ✅ **Error handling**: Comprehensive error management APIs

## Performance & Cost Benefits

### Performance Improvements
1. **Eliminated Queue Delays**: Instant processing vs background job waiting
2. **Reduced Server Load**: CPU/memory freed for other operations  
3. **Better User Experience**: Real-time progress and immediate feedback
4. **Improved Scalability**: Processing scales with users, not server capacity
5. **Reduced Latency**: No R2 download/upload round-trips

### Cost Savings
1. **Server Resources**: 60-80% reduction in CPU/memory usage for audio processing
2. **Storage Costs**: Eliminate temporary file storage on servers
3. **Bandwidth**: Remove R2 → server → R2 transfer costs
4. **Infrastructure**: Potential server downsizing opportunities
5. **Queue Workers**: Reduced background processing requirements

## Implementation Plan

### Phase 1: Frontend Integration (Week 1) **COMPLETED**

#### Install Dependencies
```bash
npm install mediabunny
```

#### Create Audio Processing Hook
```typescript
// hooks/useClientAudioProcessing.ts
import { useState, useCallback } from 'react';
import { 
  Input, 
  Output, 
  Conversion, 
  VorbisOutputFormat, 
  BlobSource, 
  BufferTarget, 
  ALL_FORMATS 
} from 'mediabunny';

interface ProcessedAudioData {
  processedFile: File;
  duration: number;
  originalSize: number;
  processedSize: number;
}

interface UseClientAudioProcessingReturn {
  processAudioFile: (file: File) => Promise<ProcessedAudioData>;
  progress: number;
  error: string | null;
  isProcessing: boolean;
  isSupported: boolean;
}

export function useClientAudioProcessing(): UseClientAudioProcessingReturn {
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Check browser compatibility
  const isSupported = 'VideoDecoder' in window && 'VideoEncoder' in window;

  const processAudioFile = useCallback(async (file: File): Promise<ProcessedAudioData> => {
    if (!isSupported) {
      throw new Error('Browser does not support WebCodecs API');
    }

    setIsProcessing(true);
    setError(null);
    setProgress(0);

    try {
      const input = new Input({
        source: new BlobSource(file),
        formats: ALL_FORMATS,
      });
      
      const output = new Output({
        format: new VorbisOutputFormat(),
        target: new BufferTarget(),
      });
      
      const conversion = await Conversion.init({
        input,
        output,
        audio: {
          codec: 'vorbis',
          bitrate: 128000, // 128kbps to match server processing
          numberOfChannels: 2, // stereo
        },
      });

      // Track conversion progress
      conversion.on('progress', (progressData) => {
        setProgress(Math.round(progressData.percentage));
      });

      await conversion.execute();
      
      const processedBuffer = output.target.buffer;
      const processedFile = new File(
        [processedBuffer], 
        file.name.replace(/\.[^/.]+$/, '.ogg'),
        { type: 'audio/ogg' }
      );

      // Extract duration from original input
      const duration = await input.computeDuration();
      
      setProgress(100);
      
      return {
        processedFile,
        duration,
        originalSize: file.size,
        processedSize: processedBuffer.byteLength,
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown processing error';
      setError(errorMessage);
      throw new Error(`Audio processing failed: ${errorMessage}`);
    } finally {
      setIsProcessing(false);
    }
  }, [isSupported]);

  return {
    processAudioFile,
    progress,
    error,
    isProcessing,
    isSupported,
  };
}
```

#### Update Upload Form Component Integration Points

**1. `resources/js/components/music-library-upload-form.tsx`**
- Replace existing `useAudioFileHandler` with enhanced version
- Add client-side processing integration
- Show conversion progress alongside upload progress
- Handle browser compatibility gracefully

**2. `resources/js/hooks/useAudioFileHandler.ts`** 
- Extend to integrate with `useClientAudioProcessing`
- Add processed file state management
- Maintain existing metadata extraction for UI display

**3. `resources/js/pages/uploads/create.tsx`**
- Update form submission logic to handle pre-processed files
- Add feature flag detection
- Implement fallback flow for unsupported browsers

### Phase 2: Backend Modifications (Week 2)

#### Add Feature Flag
```php
// config/app.php
'client_side_audio_processing' => env('CLIENT_SIDE_PROCESSING', false),
```

#### Update Upload Controller Integration Points

**1. `app/Http/Controllers/UploadController.php`**

Modify the `store` method to detect client-processed files:

```php
public function store(StoreUploadRequest $request)
{
    $user = Auth::user();
    $file = $request->file('audio_file');
    $isClientProcessed = $request->boolean('client_processed', false);
    
    if (config('app.client_side_audio_processing') && $isClientProcessed) {
        return $this->storeClientProcessedUpload($request, $user, $file);
    }
    
    // Existing server-side processing flow
    $uploadData = $this->prepareUploadData($request, $file);
    // ... rest of existing logic
}

private function storeClientProcessedUpload(StoreUploadRequest $request, $user, $file)
{
    $uploadData = [
        'title' => $request->input('title'),
        'description' => $request->input('description', ''),
        'filename' => $request->input('original_filename', $file->getClientOriginalName()),
        'mime_type' => 'audio/ogg', // Client always processes to OGG
        'size' => $request->input('original_size', $file->getSize()),
        'status' => 'ready', // Skip processing queue
        'duration_seconds' => $request->input('duration'),
    ];

    // Store the pre-processed OGG file directly as stream file
    $uploadData = $this->storeProcessedFile($file, $user, $uploadData);
    $upload = $this->createUploadRecord($user, $uploadData);
    
    // Broadcast ready event immediately
    \\App\\Events\\UploadProcessed::dispatch($upload);

    return redirect()->route('uploads.index')
        ->with('success', 'Audio file uploaded and processed successfully!');
}
```

**2. `app/Http/Requests/StoreUploadRequest.php`**

Update validation rules to handle client-processed uploads:

```php
public function rules(): array
{
    $rules = [
        'title' => 'required|string|max:255',
        'description' => 'nullable|string|max:1000',
    ];

    if ($this->boolean('client_processed')) {
        $rules['audio_file'] = [
            'required',
            'file',
            'mimes:ogg', // Only OGG for processed files
            'max:25000', // Processed files are typically smaller
        ];
        $rules['original_filename'] = 'required|string';
        $rules['original_size'] = 'required|integer|min:1';
        $rules['duration'] = 'required|numeric|min:0';
    } else {
        $rules['audio_file'] = [
            'required',
            'file',
            'mimes:mp3,wav,aiff,ogg,flac',
            'max:50000', // 50MB max file size
        ];
    }

    return $rules;
}
```

**3. New Storage Method**

Add method to handle pre-processed file storage:

```php
private function storeProcessedFile($file, $user, array $uploadData): array
{
    $filename = Str::slug($uploadData['title']) . '-' . Str::uuid() . '.ogg';
    $disk = config('filesystems.default');
    $date = now();

    if ($disk === 'r2') {
        // Store directly to public bucket since it's already processed
        $streamPath = sprintf('uploads/stream/%s/%s/%s', 
            $user->id, 
            $date->format('Y/m/d'), 
            $filename
        );
        
        $file->storeAs(
            dirname($streamPath), 
            basename($streamPath), 
            'r2_public'
        );
        
        return array_merge($uploadData, [
            'stream_path' => $streamPath,
            'path' => $streamPath, // Same as stream for processed files
            'uses_r2_storage' => true,
        ]);
    }
    
    // Local storage
    $streamPath = sprintf('uploads/stream/%s/%s/%s', 
        $user->id, 
        $date->format('Y/m/d'), 
        $filename
    );
    
    $file->storeAs(dirname($streamPath), basename($streamPath), 'public');
    
    return array_merge($uploadData, [
        'stream_path' => $streamPath,
        'path' => $streamPath,
        'uses_r2_storage' => false,
    ]);
}
```

#### Database Schema (No Changes Required)
- Existing `uploads` table structure is fully compatible
- `stream_path`, `duration_seconds`, etc. fields work as-is
- `status` field supports immediate 'ready' state
- All existing relationships and methods remain functional

### Phase 3: Gradual Rollout (Week 2-3)

#### A/B Testing Implementation
- Feature flag controls processing method
- Monitor performance metrics
- Compare error rates between approaches
- Collect user feedback on processing speed

#### Fallback Strategy
- Keep existing `ProcessAudioUpload` job active
- Automatic fallback for unsupported browsers
- Manual fallback option in UI
- Error recovery mechanisms

### Phase 4: Full Migration (Week 3)

#### Production Rollout
- Enable client-side processing for all users
- Monitor system performance metrics
- Track cost savings realization
- Update documentation and monitoring

#### Cleanup Phase
- Remove FFmpeg dependencies from servers
- Deprecate `ProcessAudioUpload` job
- Clean up temporary file storage logic
- Update error handling and logging

## Technical Implementation Details

### MediaBunny Integration Example
```typescript
import { Input, Output, Conversion, VorbisOutputFormat, BlobSource, BufferTarget } from 'mediabunny';

async function convertToOggVorbis(file: File): Promise<ArrayBuffer> {
  const input = new Input({
    source: new BlobSource(file),
    formats: ALL_FORMATS,
  });
  
  const output = new Output({
    format: new VorbisOutputFormat(),
    target: new BufferTarget(),
  });
  
  const conversion = await Conversion.init({
    input,
    output,
    audio: {
      codec: 'vorbis',
      bitrate: 128000, // 128kbps
      numberOfChannels: 2, // stereo
    },
  });
  
  await conversion.execute();
  return output.target.buffer;
}
```

### Browser Compatibility Strategy
```typescript
// Check for WebCodecs support
if ('VideoDecoder' in window && 'VideoEncoder' in window) {
  // Use MediaBunny with hardware acceleration
} else {
  // Fallback to server-side processing
  // Or use MediaBunny's software fallback
}
```

### Complete Frontend Integration Examples

**1. Enhanced Upload Form Component**
```typescript
// resources/js/components/music-library-upload-form.tsx (key changes)
import { useClientAudioProcessing } from '@/hooks/useClientAudioProcessing';

export function MusicLibraryUploadForm({ ... }: MusicLibraryUploadFormProps) {
    const {
        processAudioFile,
        progress: processingProgress,
        error: processingError,
        isProcessing,
        isSupported
    } = useClientAudioProcessing();
    
    const [processedFile, setProcessedFile] = useState<File | null>(null);
    const [originalFileData, setOriginalFileData] = useState<{
        name: string;
        size: number;
        duration: number;
    } | null>(null);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        handleAudioFileChange(e); // Existing metadata extraction

        // Process file on client if supported and enabled
        if (isSupported && config('client_side_processing')) {
            try {
                const result = await processAudioFile(file);
                setProcessedFile(result.processedFile);
                setOriginalFileData({
                    name: file.name,
                    size: file.size,
                    duration: result.duration,
                });
                setData('audio_file', result.processedFile);
            } catch (error) {
                console.error('Client processing failed, using original file:', error);
                setData('audio_file', file); // Fallback to server processing
            }
        } else {
            setData('audio_file', file); // Server processing
        }
    };

    // Rest of component with enhanced progress display
    return (
        <Card>
            {/* ... existing JSX ... */}
            
            {/* Show processing progress */}
            {isProcessing && (
                <div className="px-6 pb-4">
                    <div className="border-2 border-border bg-main-foreground p-4">
                        <div className="flex justify-between items-center mb-2">
                            <span className="font-heading font-black text-secondary-background uppercase">
                                Converting Audio...
                            </span>
                            <span className="font-mono text-chart-1">{processingProgress}%</span>
                        </div>
                        <NeoProgressBar value={processingProgress} color="bg-chart-1" />
                    </div>
                </div>
            )}
            
            {/* Show file comparison if processed */}
            {processedFile && originalFileData && (
                <div className="px-6 pb-4">
                    <div className="text-sm text-green-600">
                        ✅ Processed: {originalFileData.name} → {processedFile.name}
                        <br />Size: {formatFileSize(originalFileData.size)} → {formatFileSize(processedFile.size)}
                    </div>
                </div>
            )}
        </Card>
    );
}
```

**2. Updated Form Submission**
```typescript
// resources/js/pages/uploads/create.tsx (key changes)
const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('description', data.description);
    formData.append('audio_file', data.audio_file);
    
    // Add client processing metadata if applicable
    if (processedFile && originalFileData) {
        formData.append('client_processed', 'true');
        formData.append('original_filename', originalFileData.name);
        formData.append('original_size', originalFileData.size.toString());
        formData.append('duration', originalFileData.duration.toString());
    }
    
    post(route('uploads.store'), {
        data: formData,
        forceFormData: true,
        preserveScroll: true,
        onProgress: (progress) => {
            if (progress && typeof progress.percentage === 'number') {
                setUploadProgress(progress.percentage);
            }
        },
        onSuccess: () => reset(),
        onFinish: () => setUploadProgress(0),
    });
};
```

**3. Browser Compatibility Detection**
```typescript
// resources/js/lib/browser-support.ts
export const checkMediaBunnySupport = (): {
  supported: boolean;
  missingFeatures: string[];
} => {
  const missingFeatures: string[] = [];
  
  if (!('VideoDecoder' in window)) {
    missingFeatures.push('VideoDecoder');
  }
  
  if (!('VideoEncoder' in window)) {
    missingFeatures.push('VideoEncoder');
  }
  
  if (!('AudioDecoder' in window)) {
    missingFeatures.push('AudioDecoder');
  }
  
  if (!('AudioEncoder' in window)) {
    missingFeatures.push('AudioEncoder');
  }
  
  return {
    supported: missingFeatures.length === 0,
    missingFeatures,
  };
};
```

## Risk Assessment & Mitigation

### Low Risk Items
- **Storage Compatibility**: No changes needed to existing R2/local storage
- **Database Schema**: Existing structure fully compatible
- **API Compatibility**: No breaking changes to upload endpoints

### Medium Risk Items
- **Browser Compatibility**: 
  - *Risk*: WebCodecs not available in older browsers
  - *Mitigation*: Feature detection + server-side fallback

- **Large File Processing**:
  - *Risk*: Client devices may struggle with very large files
  - *Mitigation*: File size limits + progress indicators + chunked processing

### High Risk Items (None Identified)

## Testing Strategy

### Unit Testing
- Audio conversion accuracy tests
- Progress tracking verification
- Error handling scenarios
- Browser compatibility matrix

### Integration Testing  
- End-to-end upload workflow
- Storage integration validation
- Fallback mechanism testing
- Performance benchmarking

### User Acceptance Testing
- A/B test client vs server processing
- Performance perception studies
- Error recovery experience
- Mobile device compatibility

## Success Metrics

### Performance Metrics
- **Processing Time**: Target 50% reduction in total upload-to-ready time
- **Server CPU Usage**: Target 60-80% reduction during peak upload times
- **Memory Usage**: Target 70% reduction in peak memory consumption
- **Queue Length**: Eliminate audio processing queue backlog

### Cost Metrics
- **Server Costs**: Measurable reduction in compute instances needed
- **Storage Costs**: Eliminate temporary file storage costs
- **Bandwidth Costs**: Reduce R2 transfer costs

### User Experience Metrics
- **Upload Success Rate**: Maintain >99% success rate
- **User Satisfaction**: Measure perceived upload speed improvement
- **Error Recovery**: Reduce user-facing error rates

## Timeline & Resources

### Development Timeline: 3 Weeks Total
- **Week 1**: Frontend integration and basic processing
- **Week 2**: Backend modifications and feature flag implementation
- **Week 3**: Testing, rollout, and cleanup

### Required Resources
- **1 Frontend Developer**: MediaBunny integration and UI updates
- **1 Backend Developer**: Laravel modifications and feature flags
- **1 DevOps Engineer**: Monitoring and infrastructure optimization
- **QA Support**: Testing across browsers and devices

## Implementation Checklist

### Phase 1: Frontend Integration
- [ ] Install MediaBunny: `npm install mediabunny`
- [ ] Create `hooks/useClientAudioProcessing.ts` with full MediaBunny integration
- [ ] Update `components/music-library-upload-form.tsx`:
  - [ ] Import and integrate `useClientAudioProcessing` hook
  - [ ] Add client-side processing progress UI
  - [ ] Add processed file comparison display
  - [ ] Handle browser compatibility gracefully
- [ ] Extend `hooks/useAudioFileHandler.ts`:
  - [ ] Add integration with client processing
  - [ ] Maintain existing metadata extraction
  - [ ] Add processed file state management
- [ ] Update `pages/uploads/create.tsx`:
  - [ ] Modify form submission to include processing metadata
  - [ ] Add fallback logic for unsupported browsers
- [ ] Create `lib/browser-support.ts` for compatibility detection
- [ ] Add TypeScript types for processed audio data

### Phase 2: Backend Integration
- [ ] Add feature flag to `config/app.php`: `CLIENT_SIDE_PROCESSING`
- [ ] Update `app/Http/Controllers/UploadController.php`:
  - [ ] Modify `store` method to detect client-processed files
  - [ ] Add `storeClientProcessedUpload` private method
  - [ ] Add `storeProcessedFile` private method for direct stream storage
  - [ ] Ensure immediate 'ready' status for processed files
  - [ ] Broadcast `UploadProcessed` event immediately
- [ ] Update `app/Http/Requests/StoreUploadRequest.php`:
  - [ ] Add conditional validation rules for client-processed files
  - [ ] Add validation for metadata fields (original_filename, original_size, duration)
  - [ ] Restrict processed files to OGG format only
- [ ] Test both processing paths work correctly
- [ ] Verify R2 and local storage compatibility

### Phase 3: Testing & Validation
- [ ] Unit Tests:
  - [ ] Test `useClientAudioProcessing` hook with various audio formats
  - [ ] Test browser compatibility detection
  - [ ] Test error handling in client processing
  - [ ] Test fallback to server processing
- [ ] Integration Tests:
  - [ ] Test complete upload flow with client processing
  - [ ] Test upload flow with server processing (fallback)
  - [ ] Test file storage to both R2 and local storage
  - [ ] Test metadata extraction and preservation
- [ ] Browser Compatibility Tests:
  - [ ] Chrome (latest)
  - [ ] Firefox (latest)
  - [ ] Safari (latest)
  - [ ] Edge (latest)
  - [ ] Mobile browsers (iOS Safari, Chrome Mobile)
- [ ] Performance Tests:
  - [ ] Test with various file sizes (1MB to 50MB)
  - [ ] Test with various audio formats (MP3, WAV, FLAC, etc.)
  - [ ] Measure processing time vs file size
  - [ ] Compare client vs server processing performance

### Phase 4: Deployment & Monitoring
- [ ] Deploy with feature flag disabled initially
- [ ] Set up monitoring for:
  - [ ] Client processing success/failure rates
  - [ ] Processing time metrics
  - [ ] Browser compatibility issues
  - [ ] Server resource usage reduction
- [ ] Gradual rollout:
  - [ ] Enable for 10% of users initially
  - [ ] Monitor metrics for 48 hours
  - [ ] Increase to 50% if metrics are positive
  - [ ] Full rollout after successful 50% deployment
- [ ] Documentation:
  - [ ] Update README with new processing flow
  - [ ] Document feature flag usage
  - [ ] Update API documentation for new request parameters

## Rollback Plan

### Immediate Rollback (< 1 hour)
1. Disable `CLIENT_SIDE_PROCESSING` feature flag
2. All new uploads revert to server-side processing
3. Existing processed files remain unaffected

### Full Rollback (< 4 hours)
1. Revert frontend components to previous version
2. Re-enable all background processing workers
3. Restore FFmpeg processing infrastructure

## Conclusion

The migration to MediaBunny client-side audio processing represents a strategic improvement to Beat Forge's architecture that will:

1. **Reduce Infrastructure Costs** by 60-80% for audio processing
2. **Improve User Experience** with real-time processing feedback
3. **Increase System Scalability** by moving processing to client devices
4. **Maintain Full Compatibility** with existing storage and database systems
5. **Enable Future Enhancements** with MediaBunny's rich feature set

The implementation plan provides a safe, phased approach with comprehensive fallback options and thorough testing. The migration is technically sound, financially beneficial, and poses minimal risk to the existing system.

**Recommendation: Proceed with implementation starting with Phase 1.**
