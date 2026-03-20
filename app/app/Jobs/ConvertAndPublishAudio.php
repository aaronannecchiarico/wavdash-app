<?php

namespace App\Jobs;

use App\Models\Upload;
use App\Services\AudioConversionService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class ConvertAndPublishAudio implements ShouldQueue
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
    public $timeout = 300;

    /**
     * The upload instance.
     *
     * @var \App\Models\Upload
     */
    protected $upload;

    /**
     * The source file path.
     *
     * @var string
     */
    protected $sourceFilePath;

    /**
     * The public file path.
     *
     * @var string
     */
    protected $publicFilePath;

    /**
     * The file type being processed.
     *
     * @var string
     */
    protected $fileType;

    /**
     * Optional stem type for stems processing.
     *
     * @var string|null
     */
    protected $stemType;

    /**
     * Create a new job instance.
     */
    public function __construct(
        Upload $upload,
        string $sourceFilePath,
        string $publicFilePath,
        string $fileType = 'stem',
        ?string $stemType = null
    ) {
        $this->upload = $upload;
        $this->sourceFilePath = $sourceFilePath;
        $this->publicFilePath = $publicFilePath;
        $this->fileType = $fileType;
        $this->stemType = $stemType;
    }

    /**
     * Execute the job.
     */
    public function handle(AudioConversionService $audioConversionService): void
    {
        Log::info('ConvertAndPublishAudio - Starting job', [
            'upload_id' => $this->upload->id,
            'source_file_path' => $this->sourceFilePath,
            'public_file_path' => $this->publicFilePath,
            'file_type' => $this->fileType,
            'stem_type' => $this->stemType,
            'uses_r2_storage' => $this->upload->usesR2Storage(),
        ]);

        try {
            $finalPublicPath = $audioConversionService->convertAndPublishAudio(
                $this->upload,
                $this->sourceFilePath,
                $this->publicFilePath,
                $this->fileType
            );

            if ($finalPublicPath) {
                $this->updateUploadRecord($finalPublicPath);

                Log::info('ConvertAndPublishAudio - Job completed successfully', [
                    'upload_id' => $this->upload->id,
                    'final_public_path' => $finalPublicPath,
                    'file_type' => $this->fileType,
                ]);

                // Check if all stems for this upload are now converted — if so, push to device
                if ($this->fileType === 'stem') {
                    $upload = $this->upload->fresh();
                    $totalStems = $upload->stems()->count();
                    $convertedStems = $upload->stems()->where('converted_to_ogg', true)->count();

                    Log::debug('ConvertAndPublishAudio - Checking stem conversion status', [
                        'upload_id' => $this->upload->id,
                        'final_public_path' => $finalPublicPath,
                        'file_type' => $this->fileType,
                        'total_stems' => $totalStems,
                        'converted_stems' => $convertedStems,
                    ]);

                    if ($totalStems > 0 && $totalStems === $convertedStems) {
                        PushStemsToDevice::dispatch($upload);
                    }
                }
            } else {
                throw new \Exception('Conversion returned null path');
            }

        } catch (\Exception $e) {
            Log::error('ConvertAndPublishAudio - Job failed', [
                'upload_id' => $this->upload->id,
                'source_file_path' => $this->sourceFilePath,
                'public_file_path' => $this->publicFilePath,
                'file_type' => $this->fileType,
                'error' => $e->getMessage(),
                'error_trace' => $e->getTraceAsString(),
            ]);

            throw $e;
        }
    }

    /**
     * Update the upload record with the public file path.
     */
    private function updateUploadRecord(string $finalPublicPath): void
    {
        try {
            switch ($this->fileType) {
                case 'stream':
                    $this->upload->update([
                        'stream_path' => $finalPublicPath,
                    ]);

                    Log::info('ConvertAndPublishAudio - Updated upload with stream path', [
                        'upload_id' => $this->upload->id,
                        'stream_path' => $finalPublicPath,
                    ]);
                    break;

                case 'stem':
                    // For stems, we need to update the stem record with the final OGG path
                    if ($this->stemType) {
                        $stem = $this->upload->stems()
                            ->where('stem_type', $this->stemType)
                            ->latest()
                            ->first();

                        if ($stem) {
                            $stem->update([
                                'public_path' => $finalPublicPath,
                                'converted_to_ogg' => true,
                            ]);

                            Log::info('ConvertAndPublishAudio - Updated stem with public path', [
                                'upload_id' => $this->upload->id,
                                'stem_type' => $this->stemType,
                                'public_path' => $finalPublicPath,
                            ]);
                        }
                    }

                    // Also update the upload's stems paths array
                    $currentStems = $this->upload->r2_stems_paths ?? [];
                    if ($this->stemType && ! in_array($finalPublicPath, $currentStems)) {
                        $currentStems[$this->stemType.'_public'] = $finalPublicPath;
                        $this->upload->update([
                            'r2_stems_paths' => $currentStems,
                        ]);
                    }
                    break;

                case 'tempo':
                    // For tempo, update the tempo record with the final OGG path
                    $tempo = $this->upload->tempos()
                        ->latest()
                        ->first();

                    if ($tempo) {
                        $tempo->update([
                            'public_path' => $finalPublicPath,
                            'converted_to_ogg' => true,
                        ]);

                        Log::info('ConvertAndPublishAudio - Updated tempo with public path', [
                            'upload_id' => $this->upload->id,
                            'public_path' => $finalPublicPath,
                        ]);
                    }
                    break;

                default:
                    Log::warning('ConvertAndPublishAudio - Unknown file type, no upload record update', [
                        'upload_id' => $this->upload->id,
                        'file_type' => $this->fileType,
                    ]);
            }
        } catch (\Exception $e) {
            Log::error('ConvertAndPublishAudio - Failed to update upload record', [
                'upload_id' => $this->upload->id,
                'file_type' => $this->fileType,
                'error' => $e->getMessage(),
            ]);

            // Don't throw here as the file was successfully converted and published
            // The record update failure is non-critical
        }
    }
}
