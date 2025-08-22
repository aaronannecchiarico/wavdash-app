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
     */
    public function handle(): void
    {
        // Update upload status to processing
        $this->upload->update(['status' => 'processing']);

        Log::info('ProcessAudioUpload - Starting job', [
            'upload_id' => $this->upload->id,
            'upload_path' => $this->upload->path,
            'upload_filename' => $this->upload->filename,
            'uses_r2_storage' => $this->upload->usesR2Storage(),
            'upload_status' => $this->upload->status,
        ]);

        // Validate storage compatibility before processing if audio analysis is enabled
        if (config('services.audio_analysis.enabled', false)) {
            $audioAnalysisService = app(AudioAnalysisService::class);
            $storageValidation = $audioAnalysisService->validateStorageCompatibility($this->upload);

            if (! $storageValidation['compatible']) {
                Log::warning('ProcessAudioUpload - Storage compatibility validation failed', [
                    'upload_id' => $this->upload->id,
                    'validation_result' => $storageValidation,
                ]);

                // We continue processing even if validation fails, but log the issue
                // This ensures existing functionality isn't broken if microservice is unavailable
            } else {
                Log::info('ProcessAudioUpload - Storage compatibility validated successfully', [
                    'upload_id' => $this->upload->id,
                    'validation_message' => $storageValidation['message'],
                ]);
            }
        }

        $tempFilePath = null;

        try {
            $filename = pathinfo($this->upload->filename, PATHINFO_FILENAME);
            $duration = 0;
            $defaultDisk = config('filesystems.default');

            Log::info('ProcessAudioUpload - Configuration', [
                'default_disk' => $defaultDisk,
                'upload_uses_r2' => $this->upload->usesR2Storage(),
                'filename_without_ext' => $filename,
                'php_temp_dir' => sys_get_temp_dir(),
                'upload_model_data' => $this->upload->toArray(),
            ]);

            // Handle different storage types based on upload's actual storage type
            if ($this->upload->usesR2Storage()) {
                Log::info('ProcessAudioUpload - Processing R2 file', [
                    'r2_upload_path' => $this->upload->r2_upload_path,
                    'uses_r2_storage' => $this->upload->uses_r2_storage,
                ]);

                // Download file from R2 to temporary local storage for processing
                $tempFilePath = $this->downloadFromR2ToTemp();

                if (! $tempFilePath) {
                    throw new \Exception('Failed to download file from R2 for processing');
                }

                Log::info('ProcessAudioUpload - Opening temp file with FFmpeg', [
                    'temp_file_path' => $tempFilePath,
                    'temp_file_exists' => file_exists($tempFilePath),
                    'temp_file_size' => file_exists($tempFilePath) ? filesize($tempFilePath) : 'N/A',
                ]);

                // Create a temporary disk configuration that uses the system temp directory
                // This allows FFMpeg to work with the absolute path correctly
                $tempDirPath = sys_get_temp_dir();
                $tempFileName = basename($tempFilePath);

                // Create filesystem adapter for temp directory
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
                    'full_temp_path' => $tempFilePath,
                    'file_exists_in_temp_dir' => file_exists($tempDirPath . '/' . $tempFileName),
                ]);

                // Use the temporary disk with just the filename
                $ffmpeg = FFMpeg::fromFilesystem($tempDisk)->open($tempFileName);
            } else {
                // Use local storage processing
                $storageDisk = $defaultDisk === 'local' ? 'private' : $defaultDisk;

                Log::info('ProcessAudioUpload - Processing local file', [
                    'storage_disk' => $storageDisk,
                    'upload_path' => $this->upload->path,
                    'absolute_path' => Storage::disk($storageDisk)->path($this->upload->path),
                    'file_exists' => Storage::disk($storageDisk)->exists($this->upload->path),
                    'file_size' => Storage::disk($storageDisk)->exists($this->upload->path) ? Storage::disk($storageDisk)->size($this->upload->path) : 'N/A',
                ]);

                if (! Storage::disk($storageDisk)->exists($this->upload->path)) {
                    throw new \Exception("Source file does not exist at path: {$this->upload->path} on disk: {$storageDisk}");
                }

                Log::info('ProcessAudioUpload - Opening file with FFmpeg', [
                    'storage_disk' => $storageDisk,
                    'file_path' => $this->upload->path,
                ]);

                $ffmpeg = FFMpeg::fromDisk($storageDisk)->open($this->upload->path);

                Log::info('ProcessAudioUpload - FFmpeg opened successfully', [
                    'upload_id' => $this->upload->id,
                ]);
            }

            Log::info('ProcessAudioUpload - Getting file duration', [
                'upload_id' => $this->upload->id,
            ]);

            $duration = $ffmpeg->getDurationInSeconds();

            Log::info('ProcessAudioUpload - Duration obtained', [
                'upload_id' => $this->upload->id,
                'duration_seconds' => $duration,
            ]);

            // Process to streamable format
            $extension = 'ogg';
            $destinationFilename = Str::slug($filename).'-'.Str::uuid().'.'.$extension;

            Log::info('ProcessAudioUpload - Preparing export', [
                'destination_filename' => $destinationFilename,
                'export_format' => 'OGG Vorbis',
            ]);

            // Export to OGG format
            $format = new Vorbis;
            $format->setAudioChannels(2)->setAudioKiloBitrate(128);

            if ($this->upload->usesR2Storage()) {
                // For R2, export to temp file then upload to R2
                $tempStreamPath = sys_get_temp_dir() . '/' . $destinationFilename;

                Log::info('ProcessAudioUpload - Starting R2 export', [
                    'temp_stream_path' => $tempStreamPath,
                    'upload_id' => $this->upload->id,
                ]);

                // Create a separate disk for saving output to avoid path duplication
                // We'll use the default local disk with absolute path resolution
                $outputDir = sys_get_temp_dir();
                $outputAdapter = new LocalFilesystemAdapter($outputDir);
                $outputFlysystemFilesystem = new Filesystem($outputAdapter);
                $outputDisk = new FilesystemAdapter(
                    $outputFlysystemFilesystem,
                    $outputAdapter,
                    ['root' => $outputDir]
                );

                // Export using the output disk with just the filename
                $ffmpeg->export()->toDisk($outputDisk)->inFormat($format)->save($destinationFilename);

                Log::info('ProcessAudioUpload - R2 export completed', [
                    'temp_stream_path' => $tempStreamPath,
                    'temp_file_exists' => file_exists($tempStreamPath),
                    'temp_file_size' => file_exists($tempStreamPath) ? filesize($tempStreamPath) : 'N/A',
                ]);

                // Upload processed file to R2 with same structure as local (public/uploads/stream)
                $date = now();
                $r2StreamPath = sprintf(
                    'public/uploads/stream/%s/%s/%s',
                    $this->upload->user_id,
                    $date->format('Y/m/d'),
                    $destinationFilename
                );
                $content = file_get_contents($tempStreamPath);

                Log::info('ProcessAudioUpload - Uploading to R2', [
                    'r2_stream_path' => $r2StreamPath,
                    'content_size' => strlen($content),
                ]);

                if (Storage::disk('r2')->put($r2StreamPath, $content)) {
                    $streamPath = $r2StreamPath;
                    Log::info('Processed file uploaded to R2', ['path' => $r2StreamPath]);

                    // Clean up temp stream file
                    unlink($tempStreamPath);
                } else {
                    throw new \Exception('Failed to upload processed file to R2');
                }
            } else {
                // Use local storage with user-organized structure
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
                    'upload_id' => $this->upload->id,
                ]);

                $ffmpeg->export()->toDisk('public')->inFormat($format)->save($streamPath);

                Log::info('ProcessAudioUpload - Local export completed', [
                    'stream_path' => $streamPath,
                    'file_exists' => Storage::disk('public')->exists($streamPath),
                    'file_size' => Storage::disk('public')->exists($streamPath) ? Storage::disk('public')->size($streamPath) : 'N/A',
                ]);
            }

            // Update the upload record with the streamable path and set status to ready
            $updateData = [
                'stream_path' => $streamPath,
                'status' => 'ready',
                'duration_seconds' => $duration,
            ];

            $this->upload->update($updateData);

            // Broadcast the event
            \App\Events\UploadProcessed::dispatch($this->upload);

            Log::info('Audio file processed successfully', [
                'upload_id' => $this->upload->id,
                'storage' => $this->upload->usesR2Storage() ? 'r2' : $defaultDisk,
            ]);
        } catch (\Exception $e) {
            Log::error('Failed to process audio file', [
                'upload_id' => $this->upload->id,
                'error' => $e->getMessage(),
                'error_trace' => $e->getTraceAsString(),
                'error_file' => $e->getFile(),
                'error_line' => $e->getLine(),
                'storage_type' => $this->upload->usesR2Storage() ? 'r2' : $defaultDisk,
                'upload_path' => $this->upload->path ?? 'unknown',
                'temp_file_path' => $tempFilePath ?? 'none',
            ]);

            $this->upload->update(['status' => 'failed']);

            // Broadcast the event
            \App\Events\UploadProcessed::dispatch($this->upload);

            throw $e;
        } finally {
            // Clean up temporary file if it exists
            if ($tempFilePath && file_exists($tempFilePath)) {
                unlink($tempFilePath);
            }
        }
    }

    /**
     * Download file from R2 to temporary local storage for processing.
     */
    private function downloadFromR2ToTemp(): ?string
    {
        try {
            $tempFilePath = sys_get_temp_dir() . '/' . Str::uuid() . '_' . $this->upload->filename;

            Log::info('ProcessAudioUpload - Starting R2 download', [
                'upload_id' => $this->upload->id,
                'r2_upload_path' => $this->upload->r2_upload_path,
                'temp_file_path' => $tempFilePath,
                'r2_file_exists' => Storage::disk('r2')->exists($this->upload->r2_upload_path),
            ]);

            if (! Storage::disk('r2')->exists($this->upload->r2_upload_path)) {
                Log::error('R2 file does not exist', [
                    'upload_id' => $this->upload->id,
                    'r2_path' => $this->upload->r2_upload_path,
                ]);

                return null;
            }

            $r2Content = Storage::disk('r2')->get($this->upload->r2_upload_path);

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
            Log::error('Failed to download file from R2', [
                'upload_id' => $this->upload->id,
                'r2_path' => $this->upload->r2_upload_path,
                'error' => $e->getMessage(),
                'error_trace' => $e->getTraceAsString(),
            ]);

            return null;
        }
    }
}