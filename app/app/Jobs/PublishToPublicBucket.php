<?php

namespace App\Jobs;

use App\Models\Upload;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class PublishToPublicBucket implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    /**
     * The number of times the job may be attempted.
     *
     * @var int
     */
    public $tries = 3;

    /**
     * The number of seconds the job can run before timing out.
     *
     * @var int
     */
    public $timeout = 120;

    /**
     * The upload instance.
     *
     * @var \App\Models\Upload
     */
    protected $upload;

    /**
     * The private bucket path to copy from.
     *
     * @var string
     */
    protected $privateFilePath;

    /**
     * The public bucket path to copy to.
     *
     * @var string
     */
    protected $publicFilePath;

    /**
     * The file type being published.
     *
     * @var string
     */
    protected $fileType;

    /**
     * Create a new job instance.
     */
    public function __construct(Upload $upload, string $privateFilePath, string $publicFilePath, string $fileType = 'stream')
    {
        $this->upload = $upload;
        $this->privateFilePath = $privateFilePath;
        $this->publicFilePath = $publicFilePath;
        $this->fileType = $fileType;
    }

    public function handle(): void
    {
        Log::info('PublishToPublicBucket - Starting job', [
            'upload_id' => $this->upload->id,
            'private_file_path' => $this->privateFilePath,
            'public_file_path' => $this->publicFilePath,
            'file_type' => $this->fileType,
            'uses_r2_storage' => $this->upload->usesR2Storage(),
        ]);

        try {
            if ($this->upload->usesR2Storage()) {
                // Handle R2 storage
                $this->handleR2Storage();
            } else {
                // Handle local storage
                $this->handleLocalStorage();
            }

            // Update upload record based on file type
            $this->updateUploadRecord();

        } catch (\Exception $e) {
            Log::error('PublishToPublicBucket - Job failed', [
                'upload_id' => $this->upload->id,
                'private_file_path' => $this->privateFilePath,
                'public_file_path' => $this->publicFilePath,
                'file_type' => $this->fileType,
                'error' => $e->getMessage(),
                'error_trace' => $e->getTraceAsString(),
            ]);

            throw $e;
        }
    }

    /**
     * Handle R2 storage file copying.
     */
    private function handleR2Storage(): void
    {
        // Check if private file exists
        if (! Storage::disk('r2_private')->exists($this->privateFilePath)) {
            Log::error('PublishToPublicBucket - Private file does not exist', [
                'upload_id' => $this->upload->id,
                'private_file_path' => $this->privateFilePath,
            ]);
            throw new \Exception("Private file does not exist: {$this->privateFilePath}");
        }

        // Get file content from private bucket
        $fileContent = Storage::disk('r2_private')->get($this->privateFilePath);

        if (! $fileContent) {
            Log::error('PublishToPublicBucket - Failed to read private file content', [
                'upload_id' => $this->upload->id,
                'private_file_path' => $this->privateFilePath,
            ]);
            throw new \Exception("Failed to read private file content: {$this->privateFilePath}");
        }

        Log::info('PublishToPublicBucket - File content retrieved from private bucket', [
            'upload_id' => $this->upload->id,
            'content_size' => strlen($fileContent),
        ]);

        // Copy file to public bucket
        $success = Storage::disk('r2_public')->put($this->publicFilePath, $fileContent);

        if (! $success) {
            Log::error('PublishToPublicBucket - Failed to upload to public bucket', [
                'upload_id' => $this->upload->id,
                'public_file_path' => $this->publicFilePath,
            ]);
            throw new \Exception("Failed to upload to public bucket: {$this->publicFilePath}");
        }

        Log::info('PublishToPublicBucket - File successfully published to public bucket', [
            'upload_id' => $this->upload->id,
            'public_file_path' => $this->publicFilePath,
            'file_type' => $this->fileType,
            'content_size' => strlen($fileContent),
        ]);
    }

    /**
     * Handle local storage file copying.
     */
    private function handleLocalStorage(): void
    {
        // Build full paths for local storage
        $privateFullPath = storage_path('app/'.$this->privateFilePath);
        $publicFullPath = storage_path('app/public/'.$this->publicFilePath);

        // Check if private file exists
        if (! file_exists($privateFullPath)) {
            Log::error('PublishToPublicBucket - Private file does not exist', [
                'upload_id' => $this->upload->id,
                'private_file_path' => $this->privateFilePath,
                'private_full_path' => $privateFullPath,
            ]);
            throw new \Exception("Private file does not exist: {$privateFullPath}");
        }

        // Create directory if it doesn't exist
        $publicDir = dirname($publicFullPath);
        if (! is_dir($publicDir)) {
            if (! mkdir($publicDir, 0755, true)) {
                Log::error('PublishToPublicBucket - Failed to create public directory', [
                    'upload_id' => $this->upload->id,
                    'public_directory' => $publicDir,
                ]);
                throw new \Exception("Failed to create public directory: {$publicDir}");
            }
        }

        // Copy file to public directory
        if (! copy($privateFullPath, $publicFullPath)) {
            Log::error('PublishToPublicBucket - Failed to copy file to public directory', [
                'upload_id' => $this->upload->id,
                'private_full_path' => $privateFullPath,
                'public_full_path' => $publicFullPath,
            ]);
            throw new \Exception("Failed to copy file to public directory: {$publicFullPath}");
        }

        Log::info('PublishToPublicBucket - File successfully copied to public directory', [
            'upload_id' => $this->upload->id,
            'private_full_path' => $privateFullPath,
            'public_full_path' => $publicFullPath,
            'file_type' => $this->fileType,
            'file_size' => filesize($publicFullPath),
        ]);
    }

    /**
     * Update the upload record with the public file path.
     */
    private function updateUploadRecord(): void
    {
        try {
            switch ($this->fileType) {
                case 'stream':
                    $this->upload->update([
                        'stream_path' => $this->publicFilePath,
                    ]);

                    Log::info('PublishToPublicBucket - Updated upload with stream path', [
                        'upload_id' => $this->upload->id,
                        'stream_path' => $this->publicFilePath,
                    ]);
                    break;

                case 'stem':
                    // Handle stems by updating the stems paths array
                    $currentStems = $this->upload->r2_stems_paths ?? [];
                    if (! in_array($this->publicFilePath, $currentStems)) {
                        $currentStems[] = $this->publicFilePath;
                        $this->upload->update([
                            'r2_stems_paths' => $currentStems,
                        ]);

                        Log::info('PublishToPublicBucket - Updated upload with public stem path', [
                            'upload_id' => $this->upload->id,
                            'public_stem_path' => $this->publicFilePath,
                        ]);
                    }
                    break;

                case 'tempo':
                    // Handle tempo files (add a field if needed later)
                    Log::info('PublishToPublicBucket - Tempo file published', [
                        'upload_id' => $this->upload->id,
                        'tempo_file_path' => $this->publicFilePath,
                    ]);
                    break;

                default:
                    Log::warning('PublishToPublicBucket - Unknown file type, no upload record update', [
                        'upload_id' => $this->upload->id,
                        'file_type' => $this->fileType,
                    ]);
            }
        } catch (\Exception $e) {
            Log::error('PublishToPublicBucket - Failed to update upload record', [
                'upload_id' => $this->upload->id,
                'file_type' => $this->fileType,
                'error' => $e->getMessage(),
            ]);

            // Don't throw here as the file was successfully published
            // The record update failure is non-critical
        }
    }
}
