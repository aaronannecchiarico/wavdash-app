<?php

namespace App\Http\Controllers\Api;

use App\Events\AnalysisCompleted;
use App\Events\StemSeparationCompleted;
use App\Http\Controllers\Controller;
use App\Models\Upload;
use App\Models\UploadAnalysisTask;
use App\Models\UploadStemTask;
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
        Log::info('Analysis callback received', [
            'upload_id' => $upload->id,
            'request_data' => $request->all(),
            'user_agent' => $request->userAgent(),
            'ip' => $request->ip()
        ]);

        // Validate the callback data according to the new format
        try {
            $data = $request->validate([
                'task_id' => 'required|string',
                'status' => 'required|string|in:completed,failed',
                'processing_type' => 'required|string|in:features,stems',
                'storage_paths' => 'sometimes|array',
                'analysis_summary' => 'nullable|array',
                'error_message' => 'nullable|string',
                'processing_time' => 'required|numeric',
                'storage_type' => 'required|string'
            ]);
        } catch (\Illuminate\Validation\ValidationException $e) {
            Log::error('Invalid callback data format', [
                'upload_id' => $upload->id,
                'validation_errors' => $e->errors(),
                'request_data' => $request->all()
            ]);
            return response()->json(['error' => 'Invalid callback data format'], 422);
        }
        
        try {
            // Find the appropriate task based on processing type
            $task = null;
            $eventClass = null;

            if ($data['processing_type'] === 'features') {
                $task = $upload->analysisTask;
                $eventClass = AnalysisCompleted::class;
            } elseif ($data['processing_type'] === 'stems') {
                $task = $upload->stemTask;
                $eventClass = StemSeparationCompleted::class;
            }

            if (!$task) {
                Log::error('No task found for callback', [
                    'upload_id' => $upload->id,
                    'task_id' => $data['task_id'] ?? 'unknown',
                    'processing_type' => $data['processing_type'],
                    'upload_user_id' => $upload->user_id,
                    'upload_status' => $upload->status
                ]);
                return response()->json(['error' => 'Task not found'], 404);
            }

            Log::info('Task found for callback', [
                'upload_id' => $upload->id,
                'task_id' => $data['task_id'],
                'current_task_status' => $task->status,
                'expected_task_id' => $task->task_id,
                'callback_status' => $data['status'],
                'processing_type' => $data['processing_type'],
                'storage_type' => $data['storage_type'],
                'processing_time' => $data['processing_time']
            ]);

            // Verify the task ID matches
            if ($task->task_id !== $data['task_id']) {
                Log::error('Task ID mismatch in callback', [
                    'upload_id' => $upload->id,
                    'expected_task_id' => $task->task_id,
                    'received_task_id' => $data['task_id'],
                    'task_id' => $task->id,
                    'task_status' => $task->status,
                    'processing_type' => $data['processing_type']
                ]);
                return response()->json(['error' => 'Task ID mismatch'], 400);
            }

            if ($data['status'] === 'completed') {
                if ($data['processing_type'] === 'features') {
                    $this->handleCompletedAnalysis($upload, $task, $data);
                } elseif ($data['processing_type'] === 'stems') {
                    $this->handleCompletedStemSeparation($upload, $task, $data);
                }
            } elseif ($data['status'] === 'failed') {
                $this->handleFailedTask($task, $data);
            }
            
            // Verify the task status with microservice to ensure consistency
            $this->verifyTaskStatusWithMicroservice($task, $data['status']);

            // Broadcast the appropriate completion event for real-time UI updates
            Log::info('Broadcasting task completion event', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id,
                'status' => $task->status,
                'user_id' => $upload->user_id,
                'processing_type' => $data['processing_type']
            ]);
            
            broadcast(new $eventClass($upload, $task));

            Log::info('Callback processed successfully', [
                'upload_id' => $upload->id,
                'task_id' => $data['task_id'],
                'final_status' => $task->status,
                'processing_type' => $data['processing_type']
            ]);

            return response()->json([
                'status' => 'success',
                'message' => 'Callback processed successfully'
            ]);

        } catch (\Exception $e) {
            Log::error('Error processing callback', [
                'upload_id' => $upload->id,
                'task_id' => $data['task_id'] ?? 'unknown',
                'processing_type' => $data['processing_type'] ?? 'unknown',
                'error' => $e->getMessage(),
                'file' => $e->getFile(),
                'line' => $e->getLine(),
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
        Log::info('Starting to handle completed analysis', [
            'upload_id' => $upload->id,
            'task_id' => $task->task_id,
            'processing_type' => $data['processing_type'],
            'data_keys' => array_keys($data)
        ]);

        try {
            // Handle different processing types
            if ($data['processing_type'] === 'features') {
                Log::info('Processing features completion', [
                    'upload_id' => $upload->id,
                    'task_id' => $task->task_id,
                    'has_analysis_summary' => isset($data['analysis_summary']),
                    'analysis_data' => $data['analysis_summary'] ?? null
                ]);
                $this->handleFeaturesCompletion($upload, $task, $data);
            } elseif ($data['processing_type'] === 'stems') {
                Log::info('Processing stems completion', [
                    'upload_id' => $upload->id,
                    'task_id' => $task->task_id,
                    'has_storage_paths' => isset($data['storage_paths']),
                    'storage_paths' => $data['storage_paths'] ?? null
                ]);
                $this->handleStemsCompletion($upload, $task, $data);
            }

            // Update task completion
            $task->update([
                'status' => 'completed',
                'progress' => 100,
                'completed_at' => now(),
            ]);

            Log::info('Analysis task marked as completed', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id,
                'processing_type' => $data['processing_type'],
                'storage_type' => $data['storage_type'],
                'processing_time' => $data['processing_time'],
                'final_task_status' => $task->status
            ]);

        } catch (\Exception $e) {
            Log::error('Error handling completed analysis', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id,
                'processing_type' => $data['processing_type'],
                'error' => $e->getMessage(),
                'file' => $e->getFile(),
                'line' => $e->getLine(),
                'trace' => $e->getTraceAsString()
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

        Log::info('Features completion data', [
            'upload_id' => $upload->id,
            'task_id' => $task->task_id,
            'analysis_summary_keys' => array_keys($analysisData),
            'analysis_summary' => $analysisData,
            'storage_paths' => $data['storage_paths'] ?? []
        ]);

        if (empty($analysisData)) {
            Log::warning('No musical analysis data in callback, checking if analysis file exists', [
                'upload_id' => $upload->id,
                'task_id' => $task->task_id,
                'storage_paths' => $data['storage_paths'] ?? [],
                'full_callback_data' => $data
            ]);
            
            // If no analysis summary but we have storage paths, try to create a minimal analysis record
            // The analysis data might be in the stored file but not included in the callback
            if (isset($data['storage_paths']['analysis'])) {
                Log::info('Creating minimal analysis record from storage path', [
                    'upload_id' => $upload->id,
                    'task_id' => $task->task_id,
                    'analysis_file' => $data['storage_paths']['analysis']
                ]);
                
                // Create a minimal analysis record indicating the analysis was completed
                // but data is stored in the file
                $upload->analysis()->create([
                    'analysis_duration' => $data['processing_time'] ?? null,
                    'chunk_count' => null,
                    'key_changes' => 1,
                ]);
                
                Log::info('Minimal analysis record created', [
                    'upload_id' => $upload->id,
                    'task_id' => $task->task_id,
                    'analysis_file' => $data['storage_paths']['analysis']
                ]);
                return;
            }
            
            throw new \Exception('No musical analysis data received and no analysis file path provided');
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
        $analysisRecord = $upload->analysis()->create([
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
            'analysis_id' => $analysisRecord->id,
            'key' => $analysisData['key'] ?? 'unknown',
            'bpm' => isset($analysisData['bpm']) ? round($analysisData['bpm']) : 'unknown',
            'brightness' => $analysisData['brightness'] ?? 'unknown',
            'loudness_db' => $analysisData['loudness_db'] ?? 'unknown'
        ]);
    }

    /**
     * Handle stem separation completion.
     */
    private function handleCompletedStemSeparation(Upload $upload, UploadStemTask $task, array $data): void
    {
        $storagePaths = $data['storage_paths'] ?? [];
        
        // Filter out the original file path to get just the stems
        $stemPaths = array_filter($storagePaths, function($key) {
            return $key !== 'original';
        }, ARRAY_FILTER_USE_KEY);

        if (!empty($stemPaths)) {
            // Create UploadStem records for each separated stem
            foreach ($stemPaths as $stemType => $filePath) {
                // Adjust file path based on storage type
                $adjustedFilePath = $filePath;
                if (($data['storage_type'] ?? 'r2') === 'local') {
                    // For local storage, prepend 'private/' if not already present
                    if (!str_starts_with($filePath, 'private/')) {
                        $adjustedFilePath = 'private/' . $filePath;
                    }
                }
                
                $upload->stems()->create([
                    'stem_type' => $stemType,
                    'file_path' => $adjustedFilePath,
                    'storage_type' => $data['storage_type'] ?? 'r2',
                    'file_size' => null, // Will be populated later if needed
                    'duration' => $upload->duration_seconds ?? null,
                    'metadata' => [
                        'processing_time' => $data['processing_time'] ?? null,
                        'task_id' => $task->task_id,
                    ]
                ]);
            }

            // Also store stems paths in the upload record for backward compatibility
            $upload->update([
                'r2_stems_paths' => $stemPaths,
            ]);
            
            Log::info('Stem separation completed', [
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

        // Mark the stem task as completed
        $task->markCompleted();
        
        Log::info('Stem separation task marked as completed', [
            'upload_id' => $upload->id,
            'task_id' => $task->task_id,
            'final_task_status' => $task->status
        ]);
    }

    /**
     * Handle failed task (analysis or stem separation).
     */
    private function handleFailedTask($task, array $data): void
    {
        $errorMessage = $data['error_message'] ?? 'Processing failed';
        
        $task->markFailed($errorMessage);

        Log::warning('Task failed', [
            'task_id' => $task->task_id,
            'upload_id' => $task->upload_id,
            'error' => $errorMessage,
            'processing_type' => $data['processing_type'] ?? 'unknown'
        ]);
    }
    
    /**
     * Verify task status with microservice to ensure consistency.
     */
    private function verifyTaskStatusWithMicroservice($task, string $expectedStatus): void
    {
        try {
            $microserviceClient = app(\App\Services\AudioMicroserviceClient::class);
            $taskStatus = $microserviceClient->getTaskStatus($task->task_id);
            
            Log::info('Microservice task status verification', [
                'task_id' => $task->task_id,
                'upload_id' => $task->upload_id,
                'local_status' => $task->status,
                'expected_status' => $expectedStatus,
                'microservice_status' => $taskStatus['status'] ?? 'unknown',
                'microservice_response' => $taskStatus,
                'task_type' => get_class($task)
            ]);
            
            // Check if microservice status matches what we received in callback
            if (isset($taskStatus['status']) && $taskStatus['status'] !== $expectedStatus) {
                Log::warning('Task status mismatch between callback and microservice', [
                    'task_id' => $task->task_id,
                    'upload_id' => $task->upload_id,
                    'callback_status' => $expectedStatus,
                    'microservice_status' => $taskStatus['status'],
                    'local_task_status' => $task->status,
                    'task_type' => get_class($task)
                ]);
                
                // If microservice says it's completed but we received something else, update accordingly
                if ($taskStatus['status'] === 'completed' && $expectedStatus !== 'completed') {
                    Log::info('Correcting task status to completed based on microservice verification', [
                        'task_id' => $task->task_id,
                        'upload_id' => $task->upload_id,
                        'task_type' => get_class($task)
                    ]);
                    $task->markCompleted();
                }
            }
            
        } catch (\Exception $e) {
            Log::warning('Failed to verify task status with microservice', [
                'task_id' => $task->task_id,
                'upload_id' => $task->upload_id,
                'error' => $e->getMessage(),
                'expected_status' => $expectedStatus,
                'task_type' => get_class($task)
            ]);
            // Don't fail the callback processing if verification fails
        }
    }
}