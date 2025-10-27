<?php

namespace App\Services;

use App\Models\Upload;
use App\Models\UploadAnalysisTask;
use App\Models\UploadStemTask;
use App\Models\UploadTempoTask;
use Illuminate\Support\Facades\Log;

class AudioAnalysisService
{
    private AudioMicroserviceClient $client;

    public function __construct(AudioMicroserviceClient $client)
    {
        $this->client = $client;
    }

    /**
     * Submit an audio file for analysis using the new storage-based API.
     */
    public function submitForAnalysis(Upload $upload): ?UploadAnalysisTask
    {
        try {
            // Check if there's already a processing task
            if ($upload->analysisTask && $upload->analysisTask->isProcessing()) {
                Log::info('Analysis already in progress for upload', [
                    'upload_id' => $upload->id,
                    'task_id' => $upload->analysisTask->task_id,
                    'status' => $upload->analysisTask->status,
                ]);

                return null;
            }

            // Clean up any existing deleted or failed tasks before starting a new one
            if ($upload->analysisTask && ($upload->analysisTask->isDeleted() || $upload->analysisTask->hasFailed())) {
                Log::info('Removing existing deleted/failed task before starting new analysis', [
                    'upload_id' => $upload->id,
                    'old_task_status' => $upload->analysisTask->status,
                    'old_task_id' => $upload->analysisTask->task_id,
                ]);

                $upload->analysisTask->delete();
                $upload->unsetRelation('analysisTask'); // Clear the relationship cache
            }

            // Determine storage path based on how the upload was stored
            $storagePath = $upload->getFilePath();

            Log::info('Submitting upload for analysis', [
                'upload_id' => $upload->id,
                'storage_path' => $storagePath,
                'uses_r2' => $upload->usesR2Storage(),
            ]);

            // Call the microservice with the storage path
            $result = $this->client->extractFeatures($storagePath, [
                'detailed' => false, // We only need summary data
                'callback_url' => route('api.audio.analysis.callback', $upload->id),
                'metadata' => [
                    'upload_id' => (string) $upload->id,
                    'user_id' => (string) $upload->user_id,
                    'original_filename' => $upload->filename,
                ],
            ]);

            $taskId = $result['task_id'] ?? null;

            if (! $taskId) {
                Log::error('No task ID returned from analysis API', ['upload_id' => $upload->id, 'response' => $result]);

                return null;
            }

            // Create the analysis task record
            /** @var UploadAnalysisTask $analysisTask */
            $analysisTask = $upload->analysisTask()->create([
                'task_id' => $taskId,
                'status' => $result['status'] ?? 'pending',
                'progress' => 0,
                'submitted_at' => now(),
            ]);

            Log::info('Audio analysis task submitted', [
                'upload_id' => $upload->id,
                'task_id' => $taskId,
                'analysis_task_id' => $analysisTask->id,
                'storage_path' => $storagePath,
            ]);

            return $analysisTask;

        } catch (\Exception $e) {
            Log::error('Exception while submitting audio for analysis', [
                'upload_id' => $upload->id,
                'error' => $e->getMessage(),
            ]);

            return null;
        }
    }

    /**
     * Check the status of an analysis task.
     */
    public function checkTaskStatus(UploadAnalysisTask $task): bool
    {
        try {
            $result = $this->client->getTaskStatus($task->task_id);

            $status = $result['status'] ?? 'unknown';
            $progress = $result['progress'] ?? $task->progress;

            // Update task status
            $task->update([
                'status' => $status,
                'progress' => $progress,
            ]);

            // If completed, fetch the analysis results
            if ($status === 'completed') {
                $this->fetchAnalysisResults($task);
                $task->markCompleted();
            } elseif ($status === 'failed') {
                $errorMessage = $result['error'] ?? 'Analysis failed';
                $task->markFailed($errorMessage);
            }

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while checking task status', [
                'task_id' => $task->task_id,
                'error' => $e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Fetch and store the analysis results.
     */
    private function fetchAnalysisResults(UploadAnalysisTask $task): bool
    {
        try {
            $data = $this->client->getTaskSummary($task->task_id);

            // The new API returns analysis_summary directly
            $musicalAnalysis = $data['analysis_summary'] ?? [];

            if (empty($musicalAnalysis)) {
                Log::warning('No musical analysis data in response', ['task_id' => $task->task_id]);

                return false;
            }

            // Create the analysis record with the new data structure
            $task->upload->analysis()->create([
                'musical_key' => $musicalAnalysis['key'] ?? null,
                'key_confidence' => $musicalAnalysis['key_confidence'] ?? null,
                'bpm' => isset($musicalAnalysis['bpm']) ? round($musicalAnalysis['bpm']) : null,
                'beat_regularity' => $musicalAnalysis['beat_regularity'] ?? null,
                'loudness_db' => $musicalAnalysis['loudness_db'] ?? null,
                'dynamic_range_db' => $musicalAnalysis['dynamic_range_db'] ?? null,
                'brightness' => $musicalAnalysis['brightness'] ?? null,
                'timbral_complexity' => $musicalAnalysis['timbral_complexity'] ?? null,
                'analysis_duration' => $data['processing_time'] ?? null,
                'chunk_count' => $data['chunk_count'] ?? null,
                'key_changes' => $data['key_changes'] ?? 1,
            ]);

            Log::info('Analysis results stored', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'key' => $musicalAnalysis['key'] ?? 'unknown',
                'bpm' => isset($musicalAnalysis['bpm']) ? round($musicalAnalysis['bpm']) : 'unknown',
            ]);

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while fetching analysis results', [
                'task_id' => $task->task_id,
                'error' => $e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Check if the analysis service is available.
     */
    public function isServiceAvailable(): bool
    {
        return $this->client->isServiceAvailable();
    }

    /**
     * Get service status including storage information.
     */
    public function getServiceStatus(): array
    {
        try {
            $storageStatus = $this->client->getStorageStatus();

            return [
                'enabled' => config('services.audio_analysis.enabled', false),
                'available' => $this->client->isServiceAvailable(),
                'storage_type' => $storageStatus['storage_type'] ?? 'unknown',
                'storage_available' => $storageStatus['available'] ?? false,
                'storage_info' => $storageStatus,
                'base_url' => config('services.audio_analysis.base_url'),
            ];
        } catch (\Exception $e) {
            Log::warning('Failed to get storage status', ['error' => $e->getMessage()]);

            return [
                'enabled' => config('services.audio_analysis.enabled', false),
                'available' => false,
                'storage_type' => 'unknown',
                'storage_available' => false,
                'storage_info' => [],
                'base_url' => config('services.audio_analysis.base_url'),
            ];
        }
    }

    /**
     * Validate that Laravel and microservice storage configurations match.
     */
    public function validateStorageCompatibility(Upload $upload): array
    {
        try {
            $laravelStorageType = $upload->usesR2Storage() ? 'r2' : 'local';

            Log::info('AudioAnalysisService - Validating storage compatibility', [
                'upload_id' => $upload->id,
                'laravel_storage_type' => $laravelStorageType,
                'upload_uses_r2' => $upload->usesR2Storage(),
            ]);

            // Get microservice storage status
            $storageStatus = $this->client->getStorageStatus();
            $microserviceStorageType = $storageStatus['storage_type'] ?? 'unknown';
            $microserviceEnabled = $storageStatus['enabled'] ?? false;

            Log::info('AudioAnalysisService - Microservice storage status', [
                'microservice_storage_type' => $microserviceStorageType,
                'microservice_enabled' => $microserviceEnabled,
                'full_response' => $storageStatus,
            ]);

            $isCompatible = $laravelStorageType === $microserviceStorageType && $microserviceEnabled;

            $result = [
                'compatible' => $isCompatible,
                'laravel_storage_type' => $laravelStorageType,
                'microservice_storage_type' => $microserviceStorageType,
                'microservice_enabled' => $microserviceEnabled,
                'message' => $isCompatible
                    ? "Storage types match ({$laravelStorageType})"
                    : "Storage type mismatch: Laravel uses {$laravelStorageType}, microservice uses {$microserviceStorageType}",
                'microservice_status' => $storageStatus,
            ];

            Log::info('AudioAnalysisService - Storage compatibility result', [
                'upload_id' => $upload->id,
                'result' => $result,
            ]);

            return $result;

        } catch (\Exception $e) {
            Log::error('AudioAnalysisService - Storage validation failed', [
                'upload_id' => $upload->id,
                'error' => $e->getMessage(),
                'error_trace' => $e->getTraceAsString(),
            ]);

            return [
                'compatible' => false,
                'laravel_storage_type' => $upload->usesR2Storage() ? 'r2' : 'local',
                'microservice_storage_type' => 'unknown',
                'microservice_enabled' => false,
                'message' => 'Failed to validate storage compatibility: '.$e->getMessage(),
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Find similar uploads based on musical analysis.
     */
    public function findSimilarUploads(Upload $upload, int $limit = 10): \Illuminate\Database\Eloquent\Collection
    {
        $analysis = $upload->analysis;

        if (! $analysis) {
            return Upload::query()->whereRaw('1 = 0')->get();
        }

        return Upload::whereHas('analysis', function ($query) use ($analysis) {
            $query->where('upload_id', '!=', $analysis->upload_id);

            // Same key if available and reliable
            if ($analysis->hasReliableKey()) {
                $query->where('musical_key', $analysis->musical_key);
            }

            // Similar BPM (±10 BPM)
            if ($analysis->bpm) {
                $query->whereBetween('bpm', [$analysis->bpm - 10, $analysis->bpm + 10]);
            }

            // Similar brightness (±20%)
            if ($analysis->brightness) {
                $minBrightness = $analysis->brightness * 0.8;
                $maxBrightness = $analysis->brightness * 1.2;
                $query->whereBetween('brightness', [$minBrightness, $maxBrightness]);
            }

            // Require some confidence in key detection
            $query->where('key_confidence', '>', 0.7);
        })
            ->with('analysis')
            ->orderByRaw('ABS(? - (SELECT bpm FROM upload_analyses WHERE upload_id = uploads.id))', [$analysis->bpm ?? 120])
            ->limit($limit)
            ->get();
    }

    /**
     * Get file information from the microservice.
     */
    public function getFileInfo(string $storagePath): array
    {
        try {
            return $this->client->getFileInfo($storagePath);
        } catch (\Exception $e) {
            Log::error('Failed to get file info', [
                'storage_path' => $storagePath,
                'error' => $e->getMessage(),
            ]);
            throw $e;
        }
    }

    /**
     * List files in storage via the microservice.
     */
    public function listFiles(string $prefix = '', int $maxKeys = 100): array
    {
        try {
            return $this->client->listFiles($prefix, $maxKeys);
        } catch (\Exception $e) {
            Log::error('Failed to list files', [
                'prefix' => $prefix,
                'error' => $e->getMessage(),
            ]);
            throw $e;
        }
    }

    /**
     * Delete an analysis task from the microservice.
     */
    public function deleteTask(UploadAnalysisTask $task): bool
    {
        try {
            Log::info('Deleting analysis task', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'current_status' => $task->status,
            ]);

            // Call the microservice to delete the task
            $result = $this->client->deleteTask($task->task_id);

            // Update the task status to deleted
            $task->update([
                'status' => 'deleted',
                'error_message' => 'Task deleted by user',
            ]);

            // Remove any existing analysis data since we're starting fresh
            if ($task->upload->analysis) {
                $task->upload->analysis->delete();
                Log::info('Removed existing analysis data for deleted task', [
                    'upload_id' => $task->upload_id,
                    'task_id' => $task->task_id,
                ]);
            }

            Log::info('Analysis task deleted successfully', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'microservice_response' => $result,
            ]);

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while deleting analysis task', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'error' => $e->getMessage(),
            ]);

            // Still mark the task as deleted locally even if microservice call fails
            // This prevents the UI from getting stuck
            $task->update([
                'status' => 'deleted',
                'error_message' => 'Task deletion failed: '.$e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Submit an audio file for stem separation using the new storage-based API.
     */
    public function submitForStemSeparation(Upload $upload): ?UploadStemTask
    {
        try {
            // Check if there's already a processing task
            if ($upload->stemTask && $upload->stemTask->isProcessing()) {
                Log::info('Stem separation already in progress for upload', [
                    'upload_id' => $upload->id,
                    'task_id' => $upload->stemTask->task_id,
                    'status' => $upload->stemTask->status,
                ]);

                return null;
            }

            // Clean up any existing deleted or failed tasks before starting a new one
            if ($upload->stemTask && ($upload->stemTask->isDeleted() || $upload->stemTask->hasFailed())) {
                Log::info('Removing existing deleted/failed stem task before starting new separation', [
                    'upload_id' => $upload->id,
                    'old_task_status' => $upload->stemTask->status,
                    'old_task_id' => $upload->stemTask->task_id,
                ]);

                $upload->stemTask->delete();
                $upload->unsetRelation('stemTask'); // Clear the relationship cache
            }

            // Determine storage path based on how the upload was stored
            $storagePath = $upload->getFilePath();

            Log::info('Submitting upload for stem separation', [
                'upload_id' => $upload->id,
                'storage_path' => $storagePath,
                'uses_r2' => $upload->usesR2Storage(),
            ]);

            // Call the microservice for stem separation
            $result = $this->client->separateStems($storagePath, [
                'callback_url' => route('api.audio.analysis.callback', $upload->id),
                'metadata' => [
                    'upload_id' => (string) $upload->id,
                    'user_id' => (string) $upload->user_id,
                    'original_filename' => $upload->filename,
                ],
            ]);

            $taskId = $result['task_id'] ?? null;

            if (! $taskId) {
                Log::error('No task ID returned from stem separation API', ['upload_id' => $upload->id, 'response' => $result]);

                return null;
            }

            // Create the stem task record
            /** @var UploadStemTask $stemTask */
            $stemTask = $upload->stemTask()->create([
                'task_id' => $taskId,
                'status' => $result['status'] ?? 'pending',
                'progress' => 0,
                'submitted_at' => now(),
            ]);

            Log::info('Stem separation task submitted', [
                'upload_id' => $upload->id,
                'task_id' => $taskId,
                'stem_task_id' => $stemTask->id,
                'storage_path' => $storagePath,
            ]);

            return $stemTask;

        } catch (\Exception $e) {
            Log::error('Exception while submitting audio for stem separation', [
                'upload_id' => $upload->id,
                'error' => $e->getMessage(),
            ]);

            return null;
        }
    }

    /**
     * Check the status of a stem separation task.
     */
    public function checkStemTaskStatus(UploadStemTask $task): bool
    {
        try {
            $result = $this->client->getTaskStatus($task->task_id);

            $status = $result['status'] ?? 'unknown';
            $progress = $result['progress'] ?? $task->progress;

            // Update task status
            $task->update([
                'status' => $status,
                'progress' => $progress,
            ]);

            // If completed, task completion is handled by the callback
            if ($status === 'completed') {
                $task->markCompleted();
            } elseif ($status === 'failed') {
                $errorMessage = $result['error'] ?? 'Stem separation failed';
                $task->markFailed($errorMessage);
            }

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while checking stem task status', [
                'task_id' => $task->task_id,
                'error' => $e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Delete a stem separation task from the microservice.
     */
    public function deleteStemTask(UploadStemTask $task): bool
    {
        try {
            Log::info('Deleting stem separation task', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'current_status' => $task->status,
            ]);

            // Call the microservice to delete the task
            $result = $this->client->deleteTask($task->task_id);

            // Update the task status to deleted
            $task->update([
                'status' => 'deleted',
                'error_message' => 'Task deleted by user',
            ]);

            // Remove any existing stem data since we're starting fresh
            if ($task->upload->stems()->exists()) {
                $task->upload->stems()->delete();
                Log::info('Removed existing stem data for deleted task', [
                    'upload_id' => $task->upload_id,
                    'task_id' => $task->task_id,
                ]);
            }

            Log::info('Stem separation task deleted successfully', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'microservice_response' => $result,
            ]);

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while deleting stem separation task', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'error' => $e->getMessage(),
            ]);

            // Still mark the task as deleted locally even if microservice call fails
            // This prevents the UI from getting stuck
            $task->update([
                'status' => 'deleted',
                'error_message' => 'Task deletion failed: '.$e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Submit an audio file for tempo processing using the storage-based API.
     *
     * @param  array<string, mixed>  $processingOptions
     */
    public function submitForTempoProcessing(Upload $upload, array $processingOptions = []): ?UploadTempoTask
    {
        try {
            // Force refresh the relationship to avoid stale data
            $upload->unsetRelation('tempoTask');
            $upload->load('tempoTask');

            // Check if there's already a processing task
            if ($upload->tempoTask && $upload->tempoTask->isProcessing()) {
                Log::info('Tempo processing already in progress for upload', [
                    'upload_id' => $upload->id,
                    'task_id' => $upload->tempoTask->task_id,
                    'status' => $upload->tempoTask->status,
                ]);

                return null;
            }

            // Clean up any existing tasks before starting a new one (more thorough cleanup)
            if ($upload->tempoTask) {
                Log::info('Removing existing tempo task before starting new processing', [
                    'upload_id' => $upload->id,
                    'old_task_status' => $upload->tempoTask->status,
                    'old_task_id' => $upload->tempoTask->task_id,
                    'old_task_db_id' => $upload->tempoTask->id,
                ]);

                // Delete the old task
                $upload->tempoTask->delete();

                // Clear the relationship cache completely
                $upload->unsetRelation('tempoTask');
                $upload->refresh(); // Refresh the entire model to ensure clean state
            }

            // Double-check: ensure no tempo task exists for this upload
            $existingTasks = UploadTempoTask::where('upload_id', $upload->id)->get();
            if ($existingTasks->isNotEmpty()) {
                Log::warning('Found additional tempo tasks for upload, cleaning up', [
                    'upload_id' => $upload->id,
                    'task_count' => $existingTasks->count(),
                    'task_ids' => $existingTasks->pluck('task_id')->toArray(),
                ]);

                // Delete all existing tempo tasks for this upload
                UploadTempoTask::where('upload_id', $upload->id)->delete();
            }

            // Determine storage path based on how the upload was stored
            $storagePath = $upload->getFilePath();

            Log::info('Submitting upload for tempo processing', [
                'upload_id' => $upload->id,
                'storage_path' => $storagePath,
                'uses_r2' => $upload->usesR2Storage(),
                'processing_options' => $processingOptions,
            ]);

            // Call the microservice for tempo processing
            $result = $this->client->processTempo($storagePath, [
                'callback_url' => route('api.audio.analysis.callback', $upload->id),
                'metadata' => [
                    'upload_id' => (string) $upload->id,
                    'user_id' => (string) $upload->user_id,
                    'original_filename' => $upload->filename,
                ],
                ...$processingOptions,
            ]);

            $taskId = $result['task_id'] ?? null;

            if (! $taskId) {
                Log::error('No task ID returned from tempo processing API', ['upload_id' => $upload->id, 'response' => $result]);

                return null;
            }

            // Create the new tempo task record
            $tempoTask = UploadTempoTask::create([
                'upload_id' => $upload->id,
                'task_id' => $taskId,
                'status' => $result['status'] ?? 'pending',
                'progress' => 0,
                'processing_options' => $processingOptions,
                'submitted_at' => now(),
            ]);

            // Clear and reload the relationship to ensure consistency
            $upload->unsetRelation('tempoTask');
            $upload->load('tempoTask');

            Log::info('Tempo processing task submitted', [
                'upload_id' => $upload->id,
                'task_id' => $taskId,
                'tempo_task_id' => $tempoTask->id,
                'storage_path' => $storagePath,
                'processing_options' => $processingOptions,
            ]);

            return $tempoTask;

        } catch (\Exception $e) {
            $errorMessage = $e->getMessage();

            // Check for specific Celery configuration errors
            if (str_contains($errorMessage, "'function' object has no attribute 'delay'")) {
                Log::error('Celery task configuration error in tempo processing microservice', [
                    'upload_id' => $upload->id,
                    'error' => $errorMessage,
                    'processing_options' => $processingOptions,
                    'recommendation' => 'Check that tempo processing functions are decorated with @app.task in the microservice',
                ]);
            } elseif (str_contains($errorMessage, "name 'get_performance_cache' is not defined")) {
                Log::error('Missing function in tempo processing microservice', [
                    'upload_id' => $upload->id,
                    'error' => $errorMessage,
                    'processing_options' => $processingOptions,
                    'recommendation' => 'The get_performance_cache function is not defined in the microservice',
                ]);
            } else {
                Log::error('Exception while submitting audio for tempo processing', [
                    'upload_id' => $upload->id,
                    'error' => $errorMessage,
                    'processing_options' => $processingOptions,
                ]);
            }

            return null;
        }
    }

    /**
     * Check the status of a tempo processing task.
     */
    public function checkTempoTaskStatus(UploadTempoTask $task): bool
    {
        try {
            $result = $this->client->getTaskStatus($task->task_id);

            $status = $result['status'] ?? 'unknown';
            $progress = $result['progress'] ?? $task->progress;

            // Update task status
            $task->update([
                'status' => $status,
                'progress' => $progress,
            ]);

            // If completed, task completion is handled by the callback
            if ($status === 'completed') {
                $task->markCompleted();
            } elseif ($status === 'failed') {
                $errorMessage = $result['error'] ?? 'Tempo processing failed';
                $task->markFailed($errorMessage);
            }

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while checking tempo task status', [
                'task_id' => $task->task_id,
                'error' => $e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Delete a tempo processing task from the microservice.
     */
    public function deleteTempoTask(UploadTempoTask $task): bool
    {
        try {
            Log::info('Deleting tempo processing task', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'current_status' => $task->status,
            ]);

            // Call the microservice to delete the task
            $result = $this->client->deleteTask($task->task_id);

            // Update the task status to deleted
            $task->update([
                'status' => 'deleted',
                'error_message' => 'Task deleted by user',
            ]);

            // Remove any existing tempo data since we're starting fresh
            if ($task->upload->tempos()->exists()) {
                $task->upload->tempos()->delete();
                Log::info('Removed existing tempo data for deleted task', [
                    'upload_id' => $task->upload_id,
                    'task_id' => $task->task_id,
                ]);
            }

            Log::info('Tempo processing task deleted successfully', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'microservice_response' => $result,
            ]);

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while deleting tempo processing task', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'error' => $e->getMessage(),
            ]);

            // Still mark the task as deleted locally even if microservice call fails
            // This prevents the UI from getting stuck
            $task->update([
                'status' => 'deleted',
                'error_message' => 'Task deletion failed: '.$e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Get available tempo processing presets.
     */
    public function getTempoPresets(): array
    {
        try {
            return $this->client->getTempoPresets();
        } catch (\Exception $e) {
            Log::error('Failed to get tempo presets', [
                'error' => $e->getMessage(),
            ]);

            // Return default presets if microservice is unavailable
            return [
                'available_presets' => [
                    'sped_up' => [
                        'name' => 'Sped Up',
                        'tempo_factor' => 1.25,
                        'pitch_shift_semitones' => 3,
                        'description' => 'Popular chipmunk effect - faster tempo with higher pitch',
                    ],
                    'slowed_reverb' => [
                        'name' => 'Slowed + Reverb',
                        'tempo_factor' => 0.75,
                        'pitch_shift_semitones' => -2,
                        'description' => 'Dreamy slowed-down effect with atmospheric reverb',
                    ],
                    'nightcore' => [
                        'name' => 'Nightcore',
                        'tempo_factor' => 1.4,
                        'pitch_shift_semitones' => 4,
                        'description' => 'Fast tempo with high pitch and enhanced brightness',
                    ],
                    'chopped_screwed' => [
                        'name' => 'Chopped & Screwed',
                        'tempo_factor' => 0.6,
                        'pitch_shift_semitones' => -3,
                        'description' => 'Houston-style slow tempo with low-pass filtering',
                    ],
                    'custom' => [
                        'name' => 'Custom',
                        'tempo_factor' => 1.0,
                        'pitch_shift_semitones' => 0.0,
                        'description' => 'Custom tempo/pitch settings',
                    ],
                ],
            ];
        }
    }

    /**
     * Get smart tempo preset suggestions based on upload analysis.
     */
    public function getTempoSuggestions(Upload $upload): array
    {
        try {
            $params = [];

            // Use analysis data if available
            if ($upload->analysis) {
                $params['current_bpm'] = $upload->analysis->bpm;
                $params['duration_seconds'] = $upload->duration_seconds;
            }

            return $this->client->getTempoSuggestions($params);
        } catch (\Exception $e) {
            Log::error('Failed to get tempo suggestions', [
                'upload_id' => $upload->id,
                'error' => $e->getMessage(),
            ]);

            // Return default suggestions
            return [
                'suggestions' => [
                    'sped_up' => [
                        'preset' => 'sped_up',
                        'reason' => 'Create viral-ready sped-up version',
                        'optimal_factor' => 1.25,
                    ],
                    'slowed_reverb' => [
                        'preset' => 'slowed_reverb',
                        'reason' => 'Create atmospheric slowed version',
                        'optimal_factor' => 0.75,
                    ],
                ],
            ];
        }
    }
}
