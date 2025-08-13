<?php

namespace App\Services;

use App\Models\Upload;
use App\Models\UploadAnalysisTask;
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
                    'status' => $upload->analysisTask->status
                ]);
                return null;
            }

            // Clean up any existing deleted or failed tasks before starting a new one
            if ($upload->analysisTask && ($upload->analysisTask->isDeleted() || $upload->analysisTask->hasFailed())) {
                Log::info('Removing existing deleted/failed task before starting new analysis', [
                    'upload_id' => $upload->id,
                    'old_task_status' => $upload->analysisTask->status,
                    'old_task_id' => $upload->analysisTask->task_id
                ]);
                
                $upload->analysisTask->delete();
                $upload->unsetRelation('analysisTask'); // Clear the relationship cache
            }

            // Determine storage path based on how the upload was stored
            $storagePath = $upload->getFilePath();
            
            Log::info('Submitting upload for analysis', [
                'upload_id' => $upload->id,
                'storage_path' => $storagePath,
                'uses_r2' => $upload->usesR2Storage()
            ]);

            // Call the microservice with the storage path
            $result = $this->client->extractFeatures($storagePath, [
                'detailed' => false, // We only need summary data
                'callback_url' => route('api.audio.analysis.callback', $upload->id),
                'metadata' => [
                    'upload_id' => (string) $upload->id,
                    'user_id' => (string) $upload->user_id,
                    'original_filename' => $upload->filename,
                ]
            ]);

            $taskId = $result['task_id'] ?? null;

            if (!$taskId) {
                Log::error('No task ID returned from analysis API', ['upload_id' => $upload->id, 'response' => $result]);
                return null;
            }

            // Create the analysis task record
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
                'storage_path' => $storagePath
            ]);

            return $analysisTask;

        } catch (\Exception $e) {
            Log::error('Exception while submitting audio for analysis', [
                'upload_id' => $upload->id,
                'error' => $e->getMessage()
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
                'error' => $e->getMessage()
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
                'bpm' => isset($musicalAnalysis['bpm']) ? round($musicalAnalysis['bpm']) : 'unknown'
            ]);

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while fetching analysis results', [
                'task_id' => $task->task_id,
                'error' => $e->getMessage()
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
     * Find similar uploads based on musical analysis.
     */
    public function findSimilarUploads(Upload $upload, int $limit = 10): \Illuminate\Database\Eloquent\Collection
    {
        $analysis = $upload->analysis;

        if (!$analysis) {
            return collect();
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
                'error' => $e->getMessage()
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
                'error' => $e->getMessage()
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
                'current_status' => $task->status
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
                    'task_id' => $task->task_id
                ]);
            }

            Log::info('Analysis task deleted successfully', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'microservice_response' => $result
            ]);

            return true;

        } catch (\Exception $e) {
            Log::error('Exception while deleting analysis task', [
                'upload_id' => $task->upload_id,
                'task_id' => $task->task_id,
                'error' => $e->getMessage()
            ]);
            
            // Still mark the task as deleted locally even if microservice call fails
            // This prevents the UI from getting stuck
            $task->update([
                'status' => 'deleted',
                'error_message' => 'Task deletion failed: ' . $e->getMessage(),
            ]);
            
            return false;
        }
    }
}