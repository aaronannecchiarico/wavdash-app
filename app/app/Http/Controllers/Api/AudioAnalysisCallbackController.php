<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Upload;
use App\Models\UploadAnalysisTask;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Log;

class AudioAnalysisCallbackController extends Controller
{
    /**
     * Handle analysis completion callback from microservice.
     * 
     * This handles the new callback format from the unified microservice API.
     */
    public function handleAnalysisCallback(Upload $upload, Request $request): JsonResponse
    {
        // Validate the callback data according to the new format
        $data = $request->validate([
            'task_id' => 'required|string',
            'status' => 'required|string|in:completed,failed',
            'processing_type' => 'required|string|in:features,stems',
            'storage_paths' => 'sometimes|array',
            'analysis_summary' => 'sometimes|array',
            'error_message' => 'sometimes|string',
            'processing_time' => 'required|numeric',
            'storage_type' => 'required|string'
        ]);
        
        try {
            
            // Find the analysis task
            $analysisTask = $upload->analysisTask;
            if (!$analysisTask) {
                Log::error('No analysis task found for callback', [
                    'upload_id' => $upload->id,
                    'task_id' => $data['task_id'] ?? 'unknown'
                ]);
                return response()->json(['error' => 'Analysis task not found'], 404);
            }

            Log::info('Audio analysis callback received', [
                'upload_id' => $upload->id,
                'task_id' => $data['task_id'],
                'status' => $data['status'],
                'processing_type' => $data['processing_type'],
                'storage_type' => $data['storage_type']
            ]);

            // Verify the task ID matches
            if ($analysisTask->task_id !== $data['task_id']) {
                Log::error('Task ID mismatch in callback', [
                    'upload_id' => $upload->id,
                    'expected_task_id' => $analysisTask->task_id,
                    'received_task_id' => $data['task_id']
                ]);
                return response()->json(['error' => 'Task ID mismatch'], 400);
            }

            if ($data['status'] === 'completed') {
                $this->handleCompletedAnalysis($upload, $analysisTask, $data);
            } elseif ($data['status'] === 'failed') {
                $this->handleFailedAnalysis($analysisTask, $data);
            }

            return response()->json([
                'status' => 'success',
                'message' => 'Callback processed successfully'
            ]);

        } catch (\Exception $e) {
            Log::error('Error processing analysis callback', [
                'upload_id' => $upload->id,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'status' => 'error',
                'message' => 'Failed to process callback'
            ], 500);
        }
    }

    /**
     * Handle successful analysis completion.
     */
    private function handleCompletedAnalysis(Upload $upload, UploadAnalysisTask $task, array $data): void
    {
        try {
            // Handle different processing types
            if ($data['processing_type'] === 'features') {
                $this->handleFeaturesCompletion($upload, $task, $data);
            } elseif ($data['processing_type'] === 'stems') {
                $this->handleStemsCompletion($upload, $task, $data);
            }

            // Update task completion
            $task->update([
                'status' => 'completed',
                'progress' => 100,
                'completed_at' => now(),
            ]);

            Log::info('Analysis processing completed successfully', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id,
                'processing_type' => $data['processing_type'],
                'storage_type' => $data['storage_type'],
                'processing_time' => $data['processing_time']
            ]);

        } catch (\Exception $e) {
            Log::error('Error handling completed analysis', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id,
                'error' => $e->getMessage()
            ]);
            
            $task->markFailed('Error processing analysis results: ' . $e->getMessage());
        }
    }

    /**
     * Handle features extraction completion.
     */
    private function handleFeaturesCompletion(Upload $upload, UploadAnalysisTask $task, array $data): void
    {
        // Extract analysis results from the new callback format
        $analysisData = $data['analysis_summary'] ?? [];

        if (empty($analysisData)) {
            Log::warning('No musical analysis data in callback', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id
            ]);
            throw new \Exception('No musical analysis data received');
        }

        // Store processed file paths if provided
        $storagePaths = $data['storage_paths'] ?? [];
        if (isset($storagePaths['analysis'])) {
            // Store the analysis file path for future reference if needed
            Log::info('Analysis file stored', [
                'upload_id' => $upload->id,
                'analysis_path' => $storagePaths['analysis']
            ]);
        }

        // Create the analysis record using the new format
        $upload->analysis()->create([
            'musical_key' => $analysisData['key'] ?? null,
            'key_confidence' => $analysisData['key_confidence'] ?? null,
            'bpm' => isset($analysisData['bpm']) ? round($analysisData['bpm']) : null,
            'beat_regularity' => $analysisData['beat_regularity'] ?? null,
            'loudness_db' => $analysisData['loudness_db'] ?? null,
            'dynamic_range_db' => $analysisData['dynamic_range_db'] ?? null,
            'brightness' => $analysisData['brightness'] ?? null,
            'timbral_complexity' => $analysisData['timbral_complexity'] ?? null,
            'analysis_duration' => $data['processing_time'] ?? null,
            'chunk_count' => $data['chunk_count'] ?? null,
            'key_changes' => $data['key_changes'] ?? 1,
        ]);

        Log::info('Features analysis stored successfully', [
            'upload_id' => $upload->id,
            'task_id' => $task->task_id,
            'key' => $analysisData['key'] ?? 'unknown',
            'bpm' => isset($analysisData['bpm']) ? round($analysisData['bpm']) : 'unknown'
        ]);
    }

    /**
     * Handle stems separation completion.
     */
    private function handleStemsCompletion(Upload $upload, UploadAnalysisTask $task, array $data): void
    {
        $storagePaths = $data['storage_paths'] ?? [];
        
        // Filter out the original file path to get just the stems
        $stemPaths = array_filter($storagePaths, function($key) {
            return $key !== 'original';
        }, ARRAY_FILTER_USE_KEY);

        if (!empty($stemPaths)) {
            // Store stems paths in the upload record for future access
            $upload->update([
                'r2_stems_paths' => $stemPaths,
            ]);
            
            Log::info('Stems separation completed', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id,
                'stems_count' => count($stemPaths),
                'stems' => array_keys($stemPaths)
            ]);
        } else {
            Log::warning('No stem paths received in callback', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id
            ]);
        }
    }

    /**
     * Handle failed analysis.
     */
    private function handleFailedAnalysis(UploadAnalysisTask $task, array $data): void
    {
        $errorMessage = $data['error_message'] ?? 'Processing failed';
        
        $task->markFailed($errorMessage);

        Log::warning('Analysis task failed', [
            'task_id' => $task->task_id,
            'upload_id' => $task->upload_id,
            'error' => $errorMessage,
            'processing_type' => $data['processing_type'] ?? 'unknown'
        ]);
    }
}