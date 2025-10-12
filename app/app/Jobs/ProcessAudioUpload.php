<?php

namespace App\Jobs;

use App\Models\Upload;
use App\Services\AudioAnalysisService;
use FFMpeg\Format\Audio\Vorbis;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Filesystem\FilesystemAdapter;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use League\Flysystem\Filesystem;
use League\Flysystem\Local\LocalFilesystemAdapter;
use ProtoneMedia\LaravelFFMpeg\Support\FFMpeg;

/**
 * @deprecated Phase 4: Server-side audio processing has been replaced by client-side processing.
 *             This job should not be executed in Phase 4 and will throw an exception if run.
 */
class ProcessAudioUpload implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    /**
     * The number of times the job may be attempted.
     *
     * @var int
     */
    public $tries = 1;

    /**
     * The number of seconds the job can run before timing out.
     *
     * @var int
     */
    public $timeout = 300;

    /**
     * The upload instance.
     *
     * @var \App\Models\Upload
     */
    protected $upload;

    /**
     * Create a new job instance.
     */
    public function __construct(Upload $upload)
    {
        $this->upload = $upload;
    }

    /**
     * Execute the job.
     *
     * @deprecated Phase 4: Server-side audio processing is deprecated. Client-side processing is now required.
     */
    public function handle(): void
    {
        // Log deprecation warning
        Log::warning('ProcessAudioUpload job is deprecated and should not be running in Phase 4', [
            'upload_id' => $this->upload->id,
            'upload_status' => $this->upload->status,
            'message' => 'Server-side audio processing has been replaced by client-side processing. This job should not be executing.',
            'phase' => 4,
            'trace' => debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 5),
        ]);

        // Mark upload as failed since server-side processing is no longer supported
        $this->upload->update([
            'status' => 'failed',
            'error_message' => 'Server-side audio processing is no longer supported. Please re-upload using client-side processing.',
        ]);

        throw new \Exception('ProcessAudioUpload job is deprecated in Phase 4. Server-side audio processing is no longer supported.');
    }

    /**
     * Update upload status.
     */
    private function updateUploadStatus(string $status): void
    {
        $this->upload->update(['status' => $status]);
    }

    /**
     * Log job start information.
     */
    private function logJobStart(): void
    {
        Log::info('ProcessAudioUpload - Starting job', [
            'upload_id' => $this->upload->id,
            'upload_path' => $this->upload->path,
            'upload_filename' => $this->upload->filename,
            'uses_r2_storage' => $this->upload->usesR2Storage(),
            'upload_status' => $this->upload->status,
        ]);
    }

    /**
     * Validate storage compatibility for audio analysis.
     */
    private function validateStorageCompatibility(): void
    {
        if (! config('services.audio_analysis.enabled', false)) {
            return;
        }

        $audioAnalysisService = app(AudioAnalysisService::class);
        $storageValidation = $audioAnalysisService->validateStorageCompatibility($this->upload);

        if (! $storageValidation['compatible']) {
            Log::warning('ProcessAudioUpload - Storage compatibility validation failed', [
                'upload_id' => $this->upload->id,
                'validation_result' => $storageValidation,
            ]);
        } else {
            Log::info('ProcessAudioUpload - Storage compatibility validated successfully', [
                'upload_id' => $this->upload->id,
                'validation_message' => $storageValidation['message'],
            ]);
        }
    }

    /**
     * Setup FFMpeg instance based on storage type.
     */
    private function setupFFMpeg(?string &$tempFilePath)
    {
        $filename = pathinfo($this->upload->filename, PATHINFO_FILENAME);
        $defaultDisk = config('filesystems.default');

        Log::info('ProcessAudioUpload - Configuration', [
            'default_disk' => $defaultDisk,
            'upload_uses_r2' => $this->upload->usesR2Storage(),
            'filename_without_ext' => $filename,
        ]);

        if ($this->upload->usesR2Storage()) {
            return $this->setupR2FFMpeg($tempFilePath);
        }

        return $this->setupLocalFFMpeg($defaultDisk);
    }

    /**
     * Setup FFMpeg for R2 storage.
     */
    private function setupR2FFMpeg(?string &$tempFilePath)
    {
        Log::info('ProcessAudioUpload - Processing R2 file', [
            'r2_upload_path' => $this->upload->r2_upload_path,
            'uses_r2_storage' => $this->upload->uses_r2_storage,
        ]);

        $tempFilePath = $this->downloadFromR2ToTemp();

        if (! $tempFilePath) {
            throw new \Exception('Failed to download file from R2 for processing');
        }

        return $this->createTempDiskFFMpeg($tempFilePath);
    }

    /**
     * Create temporary disk FFMpeg instance.
     */
    private function createTempDiskFFMpeg(string $tempFilePath)
    {
        $tempDirPath = sys_get_temp_dir();
        $tempFileName = basename($tempFilePath);

        $adapter = new LocalFilesystemAdapter($tempDirPath);
        $flysystemFilesystem = new Filesystem($adapter);
        $tempDisk = new FilesystemAdapter(
            $flysystemFilesystem,
            $adapter,
            ['root' => $tempDirPath]
        );

        Log::info('ProcessAudioUpload - Opening with temp disk', [
            'temp_dir_path' => $tempDirPath,
            'temp_file_name' => $tempFileName,
        ]);

        return FFMpeg::fromFilesystem($tempDisk)->open($tempFileName);
    }

    /**
     * Setup FFMpeg for local storage.
     */
    private function setupLocalFFMpeg(string $defaultDisk)
    {
        $storageDisk = $defaultDisk === 'local' ? 'private' : $defaultDisk;

        Log::info('ProcessAudioUpload - Processing local file', [
            'storage_disk' => $storageDisk,
            'upload_path' => $this->upload->path,
        ]);

        if (! Storage::disk($storageDisk)->exists($this->upload->path)) {
            throw new \Exception("Source file does not exist at path: {$this->upload->path} on disk: {$storageDisk}");
        }

        return FFMpeg::fromDisk($storageDisk)->open($this->upload->path);
    }

    /**
     * Get duration from FFMpeg instance.
     */
    private function getDuration($ffmpeg): float
    {
        Log::info('ProcessAudioUpload - Getting file duration', [
            'upload_id' => $this->upload->id,
        ]);

        $duration = $ffmpeg->getDurationInSeconds();

        Log::info('ProcessAudioUpload - Duration obtained', [
            'upload_id' => $this->upload->id,
            'duration_seconds' => $duration,
        ]);

        return $duration;
    }

    /**
     * Process audio file to streamable format.
     */
    private function processAudioFile($ffmpeg): string
    {
        $filename = pathinfo($this->upload->filename, PATHINFO_FILENAME);
        $destinationFilename = Str::slug($filename).'-'.Str::uuid().'.ogg';

        Log::info('ProcessAudioUpload - Preparing export', [
            'destination_filename' => $destinationFilename,
            'export_format' => 'OGG Vorbis',
        ]);

        $format = new Vorbis;
        $format->setAudioChannels(2)->setAudioKiloBitrate(128);

        if ($this->upload->usesR2Storage()) {
            return $this->processR2Audio($ffmpeg, $format, $destinationFilename);
        }

        return $this->processLocalAudio($ffmpeg, $format, $destinationFilename);
    }

    /**
     * Process R2 audio file.
     */
    private function processR2Audio($ffmpeg, $format, string $destinationFilename): string
    {
        $tempStreamPath = sys_get_temp_dir().'/'.$destinationFilename;

        // Export to temp file
        $this->exportToTempFile($ffmpeg, $format, $destinationFilename);

        // Upload to private bucket and dispatch publish job
        return $this->uploadToR2AndDispatchPublish($tempStreamPath, $destinationFilename);
    }

    /**
     * Export audio to temporary file.
     */
    private function exportToTempFile($ffmpeg, $format, string $destinationFilename): void
    {
        $outputDir = sys_get_temp_dir();
        $outputAdapter = new LocalFilesystemAdapter($outputDir);
        $outputFlysystemFilesystem = new Filesystem($outputAdapter);
        $outputDisk = new FilesystemAdapter(
            $outputFlysystemFilesystem,
            $outputAdapter,
            ['root' => $outputDir]
        );

        $ffmpeg->export()->toDisk($outputDisk)->inFormat($format)->save($destinationFilename);
    }

    /**
     * Upload to R2 private bucket and dispatch publish job.
     */
    private function uploadToR2AndDispatchPublish(string $tempStreamPath, string $destinationFilename): string
    {
        $date = now();
        $r2PrivateStreamPath = sprintf(
            'processed/uploads/stream/%s/%s/%s',
            $this->upload->user_id,
            $date->format('Y/m/d'),
            $destinationFilename
        );

        $content = file_get_contents($tempStreamPath);

        if (! Storage::disk('r2_private')->put($r2PrivateStreamPath, $content)) {
            throw new \Exception('Failed to upload processed file to R2 private bucket');
        }

        $r2PublicStreamPath = sprintf(
            'uploads/stream/%s/%s/%s',
            $this->upload->user_id,
            $date->format('Y/m/d'),
            $destinationFilename
        );

        \App\Jobs\PublishToPublicBucket::dispatch(
            $this->upload,
            $r2PrivateStreamPath,
            $r2PublicStreamPath,
            'stream'
        );

        Log::info('PublishToPublicBucket job dispatched for stream file', [
            'upload_id' => $this->upload->id,
            'private_path' => $r2PrivateStreamPath,
            'public_path' => $r2PublicStreamPath,
        ]);

        unlink($tempStreamPath);

        return $r2PublicStreamPath;
    }

    /**
     * Process local audio file.
     */
    private function processLocalAudio($ffmpeg, $format, string $destinationFilename): string
    {
        $date = now();
        $streamPath = sprintf(
            'uploads/stream/%s/%s/%s',
            $this->upload->user_id,
            $date->format('Y/m/d'),
            $destinationFilename
        );

        Log::info('ProcessAudioUpload - Starting local export', [
            'stream_path' => $streamPath,
            'target_disk' => 'public',
        ]);

        $ffmpeg->export()->toDisk('public')->inFormat($format)->save($streamPath);

        Log::info('ProcessAudioUpload - Local export completed', [
            'stream_path' => $streamPath,
            'file_exists' => Storage::disk('public')->exists($streamPath),
        ]);

        return $streamPath;
    }

    /**
     * Finalize upload with stream path and duration.
     */
    private function finalizeUpload(string $streamPath, float $duration): void
    {
        $this->upload->update([
            'stream_path' => $streamPath,
            'status' => 'ready',
            'duration_seconds' => $duration,
        ]);
    }

    /**
     * Broadcast success event.
     */
    private function broadcastSuccess(): void
    {
        \App\Events\UploadProcessed::dispatch($this->upload);

        Log::info('Audio file processed successfully', [
            'upload_id' => $this->upload->id,
            'storage' => $this->upload->usesR2Storage() ? 'r2' : config('filesystems.default'),
        ]);
    }

    /**
     * Handle processing errors.
     */
    private function handleProcessingError(\Exception $e, ?string $tempFilePath): void
    {
        Log::error('Failed to process audio file', [
            'upload_id' => $this->upload->id,
            'error' => $e->getMessage(),
            'storage_type' => $this->upload->usesR2Storage() ? 'r2' : config('filesystems.default'),
            'upload_path' => $this->upload->path ?? 'unknown',
            'temp_file_path' => $tempFilePath ?? 'none',
        ]);

        $this->upload->update(['status' => 'failed']);
        \App\Events\UploadProcessed::dispatch($this->upload);
    }

    /**
     * Clean up temporary file.
     */
    private function cleanupTempFile(?string $tempFilePath): void
    {
        if ($tempFilePath && file_exists($tempFilePath)) {
            unlink($tempFilePath);
        }
    }

    /**
     * Download file from R2 to temporary local storage for processing.
     */
    private function downloadFromR2ToTemp(): ?string
    {
        try {
            $tempFilePath = sys_get_temp_dir().'/'.Str::uuid().'_'.$this->upload->filename;

            Log::info('ProcessAudioUpload - Starting R2 private download', [
                'upload_id' => $this->upload->id,
                'r2_upload_path' => $this->upload->r2_upload_path,
                'temp_file_path' => $tempFilePath,
                'r2_file_exists' => Storage::disk('r2_private')->exists($this->upload->r2_upload_path),
            ]);

            if (! Storage::disk('r2_private')->exists($this->upload->r2_upload_path)) {
                Log::error('R2 private file does not exist', [
                    'upload_id' => $this->upload->id,
                    'r2_path' => $this->upload->r2_upload_path,
                ]);

                return null;
            }

            $r2Content = Storage::disk('r2_private')->get($this->upload->r2_upload_path);

            Log::info('ProcessAudioUpload - R2 content retrieved', [
                'upload_id' => $this->upload->id,
                'content_size' => $r2Content ? strlen($r2Content) : 0,
                'content_retrieved' => $r2Content !== null,
            ]);

            if ($r2Content && file_put_contents($tempFilePath, $r2Content)) {
                Log::info('File downloaded from R2 to temp', [
                    'upload_id' => $this->upload->id,
                    'temp_path' => $tempFilePath,
                    'temp_file_size' => filesize($tempFilePath),
                    'temp_file_exists' => file_exists($tempFilePath),
                ]);

                return $tempFilePath;
            }

            Log::error('Failed to write R2 content to temp file', [
                'upload_id' => $this->upload->id,
                'temp_path' => $tempFilePath,
                'content_size' => $r2Content ? strlen($r2Content) : 0,
            ]);

            return null;
        } catch (\Exception $e) {
            Log::error('Failed to download file from R2 private bucket', [
                'upload_id' => $this->upload->id,
                'r2_path' => $this->upload->r2_upload_path,
                'error' => $e->getMessage(),
                'error_trace' => $e->getTraceAsString(),
            ]);

            return null;
        }
    }
}
