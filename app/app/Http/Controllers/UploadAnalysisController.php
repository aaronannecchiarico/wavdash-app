<?php

namespace App\Http\Controllers;

use App\Http\Resources\UploadResource;
use App\Models\Upload;
use App\Services\AudioAnalysisService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Inertia\Inertia;
use Inertia\Response;

class UploadAnalysisController extends Controller
{
    public function __construct(
        protected AudioAnalysisService $analysisService
    ) {}

    /**
     * Start audio analysis for an upload.
     */
    public function store(Request $request, Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        if (! config('services.audio_analysis.enabled')) {
            return redirect()->back()->with('error', 'Audio analysis is currently disabled.');
        }

        if ($upload->status !== 'ready') {
            return redirect()->back()->with('error', 'Upload must be processed before analysis can begin.');
        }

        if ($upload->analysisTask && $upload->analysisTask->isProcessing()) {
            return redirect()->back()->with('error', 'Analysis is already in progress for this upload.');
        }

        if ($upload->analysis) {
            return redirect()->back()->with('error', 'Analysis already completed for this upload.');
        }

        // Check service availability
        if (! $this->analysisService->isServiceAvailable()) {
            return redirect()->back()->with('error', 'Audio analysis service is currently unavailable.');
        }

        $analysisTask = $this->analysisService->submitForAnalysis($upload);

        if (! $analysisTask) {
            return redirect()->back()->with('error', 'Failed to submit upload for analysis.');
        }

        Log::info('Audio analysis manually triggered', [
            'upload_id' => $upload->id,
            'task_id' => $analysisTask->task_id,
            'user_id' => Auth::user()->id,
        ]);

        return redirect()->back()->with('success', 'Analysis started successfully! You will be notified when it completes.');
    }

    /**
     * Show analysis page for an upload.
     */
    public function show(Upload $upload): Response
    {
        $this->authorize('view', $upload);

        $upload->load(['analysisTask', 'analysis']);

        $analysisServiceStatus = [
            'enabled' => config('services.audio_analysis.enabled', false),
            'available' => config('services.audio_analysis.enabled') ? $this->analysisService->isServiceAvailable() : false,
        ];

        return Inertia::render('uploads/analysis', [
            'upload' => new UploadResource($upload),
            'analysis_service' => $analysisServiceStatus,
        ]);
    }

    /**
     * Delete analysis data for an upload.
     */
    public function destroy(Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        $deleted = false;

        if ($upload->analysis) {
            $upload->analysis->delete();
            $deleted = true;
            Log::info('Analysis results deleted', ['upload_id' => $upload->id]);
        }

        if ($upload->analysisTask) {
            if ($upload->analysisTask->isProcessing()) {
                return redirect()->back()->with('error', 'Cannot delete analysis while it is still processing.');
            }

            // Delete the task if it's completed, failed, or in any non-processing state
            $upload->analysisTask->delete();
            $deleted = true;
            Log::info('Analysis task deleted', [
                'upload_id' => $upload->id,
                'task_status' => $upload->analysisTask->status,
                'task_id' => $upload->analysisTask->task_id,
            ]);
        }

        if (! $deleted) {
            return redirect()->back()->with('error', 'No analysis data found to delete.');
        }

        return redirect()->back()->with('success', 'Analysis data deleted successfully.');
    }

    /**
     * Delete an active analysis task and cancel it in the microservice.
     */
    public function deleteTask(Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        if (! config('services.audio_analysis.enabled')) {
            return redirect()->back()->with('error', 'Audio analysis is currently disabled.');
        }

        if (! $upload->analysisTask) {
            return redirect()->back()->with('error', 'No analysis task found to delete.');
        }

        if (! $upload->analysisTask->canBeDeleted()) {
            return redirect()->back()->with('error', 'This analysis task cannot be deleted in its current state.');
        }

        // Check service availability
        if (! $this->analysisService->isServiceAvailable()) {
            return redirect()->back()->with('error', 'Audio analysis service is currently unavailable.');
        }

        /** @var \App\Models\UploadAnalysisTask $analysisTask */
        $analysisTask = $upload->analysisTask;
        $success = $this->analysisService->deleteTask($analysisTask);

        if ($success) {
            Log::info('Analysis task deleted via user action', [
                'upload_id' => $upload->id,
                'task_id' => $upload->analysisTask->task_id,
                'user_id' => Auth::user()->id,
            ]);

            return redirect()->back()->with('success', 'Analysis task has been cancelled and deleted. You can now start a new analysis.');
        } else {
            return redirect()->back()->with('warning', 'Analysis task was marked as deleted locally, but there may have been an issue communicating with the analysis service.');
        }
    }

    /**
     * Show similar uploads page based on analysis.
     */
    public function similar(Upload $upload): Response|RedirectResponse
    {
        $this->authorize('view', $upload);

        $upload->load(['analysis']);

        if (! $upload->analysis) {
            return redirect()->route('uploads.analysis.show', $upload)
                ->with('error', 'Upload has no analysis data to compare against.');
        }

        $similarUploads = $this->analysisService->findSimilarUploads($upload, 10);

        return Inertia::render('uploads/similar', [
            'upload' => new UploadResource($upload),
            'similar_uploads' => UploadResource::collection($similarUploads),
            'analysis_criteria' => [
                'musical_key' => $upload->analysis->musical_key,
                'bpm' => $upload->analysis->bpm,
                'brightness' => $upload->analysis->brightness,
                'key_confidence' => $upload->analysis->key_confidence,
            ],
        ]);
    }

    /**
     * Get analysis service status (API endpoint).
     */
    public function status(): JsonResponse
    {
        $status = $this->analysisService->getServiceStatus();

        return response()->json($status);
    }
}
