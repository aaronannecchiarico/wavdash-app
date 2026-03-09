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

class UploadStemController extends Controller
{
    public function __construct(
        protected AudioAnalysisService $analysisService
    ) {}

    /**
     * Start stem separation for an upload.
     */
    public function store(Request $request, Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        if (! config('services.audio_analysis.enabled')) {
            return redirect()->back()->with('error', 'Audio analysis service is currently disabled.');
        }

        if ($upload->status !== 'ready') {
            return redirect()->back()->with('error', 'Upload must be processed before stem separation can begin.');
        }

        if ($upload->stemTask && $upload->stemTask->isProcessing()) {
            return redirect()->back()->with('error', 'Stem separation is already in progress for this upload.');
        }

        // Check service availability
        if (! $this->analysisService->isServiceAvailable()) {
            return redirect()->back()->with('error', 'Audio analysis service is currently unavailable.');
        }

        // Map mode to model name
        $mode = $request->input('mode', 'standard');
        $modelMap = [
            'standard' => 'htdemucs',
            'detailed' => 'htdemucs_6s',
        ];
        $modelName = $modelMap[$mode] ?? 'htdemucs';

        $stemTask = $this->analysisService->submitForStemSeparation($upload, $modelName);

        if (! $stemTask) {
            return redirect()->back()->with('error', 'Failed to submit upload for stem separation.');
        }

        Log::info('Stem separation manually triggered', [
            'upload_id' => $upload->id,
            'task_id' => $stemTask->task_id,
            'mode' => $mode,
            'model_name' => $modelName,
            'user_id' => Auth::user()->id,
        ]);

        $modeLabel = $mode === 'detailed' ? 'Detailed (6 stems)' : 'Standard (4 stems)';

        return redirect()->back()->with('success', "{$modeLabel} stem separation started! You will be notified when it completes.");
    }

    /**
     * Show stem separation page for an upload.
     */
    public function show(Upload $upload): Response
    {
        $this->authorize('view', $upload);

        $upload->load(['stemTask', 'stems', 'analysis']);

        $analysisServiceStatus = [
            'enabled' => config('services.audio_analysis.enabled', false),
            'available' => config('services.audio_analysis.enabled') ? $this->analysisService->isServiceAvailable() : false,
        ];

        return Inertia::render('uploads/stems', [
            'upload' => new UploadResource($upload),
            'analysis_service' => $analysisServiceStatus,
        ]);
    }

    /**
     * Delete stem separation data for an upload.
     */
    public function destroy(Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        $deleted = false;

        // Delete all stems
        if ($upload->stems()->exists()) {
            $upload->stems()->delete();
            $deleted = true;
            Log::info('Stem separation results deleted', ['upload_id' => $upload->id]);
        }

        if ($upload->stemTask) {
            if ($upload->stemTask->isProcessing()) {
                return redirect()->back()->with('error', 'Cannot delete stem separation while it is still processing.');
            }

            // Delete the task if it's completed, failed, or in any non-processing state
            $upload->stemTask->delete();
            $deleted = true;
            Log::info('Stem separation task deleted', [
                'upload_id' => $upload->id,
                'task_status' => $upload->stemTask->status,
                'task_id' => $upload->stemTask->task_id,
            ]);
        }

        if (! $deleted) {
            return redirect()->back()->with('error', 'No stem separation data found to delete.');
        }

        return redirect()->back()->with('success', 'Stem separation data deleted successfully.');
    }

    /**
     * Delete an active stem separation task and cancel it in the microservice.
     */
    public function deleteTask(Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        if (! config('services.audio_analysis.enabled')) {
            return redirect()->back()->with('error', 'Audio analysis service is currently disabled.');
        }

        if (! $upload->stemTask) {
            return redirect()->back()->with('error', 'No stem separation task found to delete.');
        }

        if (! $upload->stemTask->canBeDeleted()) {
            return redirect()->back()->with('error', 'This stem separation task cannot be deleted in its current state.');
        }

        // Check service availability
        if (! $this->analysisService->isServiceAvailable()) {
            return redirect()->back()->with('error', 'Audio analysis service is currently unavailable.');
        }

        /** @var \App\Models\UploadStemTask $stemTask */
        $stemTask = $upload->stemTask;
        $success = $this->analysisService->deleteStemTask($stemTask);

        if ($success) {
            Log::info('Stem separation task deleted via user action', [
                'upload_id' => $upload->id,
                'task_id' => $upload->stemTask->task_id,
                'user_id' => Auth::user()->id,
            ]);

            return redirect()->back()->with('success', 'Stem separation task has been cancelled and deleted. You can now start a new separation.');
        } else {
            return redirect()->back()->with('warning', 'Stem separation task was marked as deleted locally, but there may have been an issue communicating with the analysis service.');
        }
    }

    /**
     * Download a specific stem file.
     */
    public function downloadStem(Upload $upload, string $stemType): mixed
    {
        $this->authorize('view', $upload);

        $stem = $upload->stems()->where('stem_type', $stemType)->first();

        if (! $stem) {
            return redirect()->back()->with('error', 'Stem not found.');
        }

        Log::info('Stem download requested', [
            'upload_id' => $upload->id,
            'stem_type' => $stemType,
            'user_id' => Auth::user()->id,
        ]);

        // If stored on R2, redirect to R2 URL
        if ($stem->isStoredOnR2()) {
            $r2Url = config('filesystems.disks.r2.url').'/'.$stem->file_path;

            return redirect()->away($r2Url);
        }

        // If stored locally, serve the file from private storage
        $filePath = $stem->file_path;

        // Handle both old and new file path formats
        if (str_starts_with($filePath, 'private/')) {
            // New format: file_path already includes 'private/'
            $fullPath = storage_path('app/'.$filePath);
        } else {
            // Old format: file_path needs 'private/' prepended
            $fullPath = storage_path('app/private/'.$filePath);
        }

        return response()->download($fullPath);
    }

    /**
     * Get stem separation service status (API endpoint).
     */
    public function status(): JsonResponse
    {
        $status = $this->analysisService->getServiceStatus();

        return response()->json($status);
    }
}
