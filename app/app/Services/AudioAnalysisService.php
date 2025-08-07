<?php

namespace App\Services;

use App\Models\Upload;
use App\Models\UploadAnalysis;
use App\Models\UploadAnalysisTask;
use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class AudioAnalysisService
{
    private string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = config('services.audio_analysis.base_url', 'http://localhost:8000');
    }

    /**
     * Submit an audio file for analysis.
     */
    public function submitForAnalysis(Upload $upload): ?UploadAnalysisTask
    {
        try {
            // Get the file path from private storage
            $filePath = Storage::disk('private')->path($upload->path);
            
            if (!file_exists($filePath)) {
                Log::error('Audio file not found for analysis', ['upload_id' => $upload->id, 'path' => $filePath]);
                return null;
            }

            // Submit to the analysis API
            $response = Http::timeout(30)
                ->attach('audio_file', file_get_contents($filePath), $upload->filename)
                ->post($this->baseUrl . '/extract-features', [
                    'async_processing' => true,
                    'extract_detailed' => false, // We only need the summary data
                ]);

            if (!$response->successful()) {
                Log::error('Failed to submit file for analysis', [
                    'upload_id' => $upload->id,
                    'status' => $response->status(),
                    'response' => $response->body()
                ]);
                return null;
            }

            $data = $response->json();
            $taskId = $data['task_id'] ?? null;

            if (!$taskId) {
                Log::error('No task ID returned from analysis API', ['upload_id' => $upload->id, 'response' => $data]);
                return null;
            }

            // Create the analysis task record
            $analysisTask = $upload->analysisTask()->create([
                'task_id' => $taskId,
                'status' => $data['status'] ?? 'pending',
                'progress' => 0,
                'submitted_at' => now(),
            ]);

            Log::info('Audio analysis task submitted', [
                'upload_id' => $upload->id,
                'task_id' => $taskId,
                'analysis_task_id' => $analysisTask->id
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
            $response = Http::timeout(10)
                ->get($this->baseUrl . "/task-status/{$task->task_id}", [
                    'include_result' => false
                ]);

            if (!$response->successful()) {
                Log::error('Failed to check task status', [
                    'task_id' => $task->task_id,
                    'status' => $response->status()
                ]);
                return false;
            }

            $data = $response->json();
            $status = $data['status'] ?? 'unknown';
            $progress = $data['progress'] ?? $task->progress;

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
                $errorMessage = $data['error'] ?? 'Analysis failed';
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
            $response = Http::timeout(10)
                ->get($this->baseUrl . "/task-summary/{$task->task_id}");

            if (!$response->successful()) {
                Log::error('Failed to fetch analysis results', [
                    'task_id' => $task->task_id,
                    'status' => $response->status()
                ]);
                return false;
            }

            $data = $response->json();
            $musicalAnalysis = $data['musical_analysis'] ?? [];
            $metadata = $data['metadata'] ?? [];

            if (empty($musicalAnalysis)) {
                Log::warning('No musical analysis data in response', ['task_id' => $task->task_id]);
                return false;
            }

            // Create the analysis record
            $task->upload->analysis()->create([
                'musical_key' => $musicalAnalysis['key'] ?? null,
                'key_confidence' => $musicalAnalysis['key_confidence'] ?? null,
                'bpm' => isset($musicalAnalysis['bpm']) ? round($musicalAnalysis['bpm']) : null,
                'beat_regularity' => $musicalAnalysis['beat_regularity'] ?? null,
                'loudness_db' => $musicalAnalysis['loudness_db'] ?? null,
                'dynamic_range_db' => $musicalAnalysis['dynamic_range_db'] ?? null,
                'brightness' => $musicalAnalysis['brightness'] ?? null,
                'timbral_complexity' => $musicalAnalysis['timbral_complexity'] ?? null,
                'analysis_duration' => $metadata['processing_time'] ?? null,
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
        try {
            $response = Http::timeout(5)->get($this->baseUrl . '/health');
            return $response->successful() && $response->json('status') === 'healthy';
        } catch (\Exception $e) {
            Log::warning('Audio analysis service unavailable', ['error' => $e->getMessage()]);
            return false;
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
}