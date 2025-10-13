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

class UploadTempoController extends Controller
{
    public function __construct(
        protected AudioAnalysisService $analysisService
    ) {}

    /**
     * Start tempo processing for an upload.
     */
    public function store(Request $request, Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        if (! config('services.audio_analysis.enabled')) {
            return redirect()->back()->with('error', 'Audio processing is currently disabled.');
        }

        if ($upload->status !== 'ready') {
            return redirect()->back()->with('error', 'Upload must be processed before tempo effects can be applied.');
        }

        if ($upload->tempoTask && $upload->tempoTask->isProcessing()) {
            return redirect()->back()->with('error', 'Tempo processing is already in progress for this upload.');
        }

        // Check service availability
        if (! $this->analysisService->isServiceAvailable()) {
            return redirect()->back()->with('error', 'Audio processing service is currently unavailable.');
        }

        // Validate tempo processing options
        $validated = $request->validate([
            'preset' => 'required|string|in:sped_up,slowed_reverb,nightcore,chopped_screwed,custom',
            'tempo_factor' => 'nullable|numeric|min:0.25|max:4.0',
            'pitch_shift_semitones' => 'nullable|numeric|min:-12|max:12',
            'preserve_pitch' => 'boolean',
            'add_reverb' => 'boolean',
            'use_stems' => 'boolean',
        ]);

        // If preset is custom, require tempo_factor
        if ($validated['preset'] === 'custom' && ! isset($validated['tempo_factor'])) {
            return redirect()->back()->with('error', 'Tempo factor is required for custom preset.');
        }

        $processingOptions = [
            'preset' => $validated['preset'],
        ];

        // Add optional parameters if provided
        if (isset($validated['tempo_factor'])) {
            $processingOptions['tempo_factor'] = $validated['tempo_factor'];
        }
        if (isset($validated['pitch_shift_semitones'])) {
            $processingOptions['pitch_shift_semitones'] = $validated['pitch_shift_semitones'];
        }
        if (isset($validated['preserve_pitch'])) {
            $processingOptions['preserve_pitch'] = $validated['preserve_pitch'];
        }
        if (isset($validated['add_reverb'])) {
            $processingOptions['add_reverb'] = $validated['add_reverb'];
        }
        if (isset($validated['use_stems'])) {
            $processingOptions['use_stems'] = $validated['use_stems'];
        }

        $tempoTask = $this->analysisService->submitForTempoProcessing($upload, $processingOptions);

        if (! $tempoTask) {
            return redirect()->back()->with('error', 'Failed to submit upload for tempo processing.');
        }

        Log::info('Tempo processing manually triggered', [
            'upload_id' => $upload->id,
            'task_id' => $tempoTask->task_id,
            'user_id' => Auth::user()->id,
            'preset' => $validated['preset'],
        ]);

        $presetName = match ($validated['preset']) {
            'sped_up' => 'Sped Up',
            'slowed_reverb' => 'Slowed + Reverb',
            'nightcore' => 'Nightcore',
            'chopped_screwed' => 'Chopped & Screwed',
            'custom' => 'Custom',
            default => ucwords(str_replace('_', ' ', $validated['preset']))
        };

        return redirect()->back()->with('success', "Tempo processing started with {$presetName} preset! You will be notified when it completes.");
    }

    /**
     * Show tempo processing page for an upload.
     */
    public function show(Upload $upload): Response
    {
        $this->authorize('view', $upload);

        $upload->load(['tempoTask', 'tempos', 'analysis']);

        $analysisServiceStatus = [
            'enabled' => config('services.audio_analysis.enabled', false),
            'available' => config('services.audio_analysis.enabled') ? $this->analysisService->isServiceAvailable() : false,
        ];

        // Get available presets
        $presets = $this->analysisService->getTempoPresets();

        // Get smart suggestions if analysis is available
        $suggestions = [];
        if ($upload->analysis) {
            $suggestions = $this->analysisService->getTempoSuggestions($upload);
        }

        return Inertia::render('uploads/tempo', [
            'upload' => new UploadResource($upload),
            'analysis_service' => $analysisServiceStatus,
            'tempo_presets' => $presets,
            'tempo_suggestions' => $suggestions,
        ]);
    }

    /**
     * Delete tempo processing task for an upload.
     */
    public function destroy(Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        $deleted = false;

        if ($upload->tempos()->exists()) {
            $upload->tempos()->delete();
            $deleted = true;
            Log::info('Tempo files deleted', ['upload_id' => $upload->id]);
        }

        if ($upload->tempoTask) {
            if ($upload->tempoTask->isProcessing()) {
                return redirect()->back()->with('error', 'Cannot delete tempo processing while it is still in progress.');
            }

            // Delete the task if it's completed, failed, or in any non-processing state
            $upload->tempoTask->delete();
            $deleted = true;
            Log::info('Tempo task deleted', [
                'upload_id' => $upload->id,
                'task_status' => $upload->tempoTask->status,
                'task_id' => $upload->tempoTask->task_id,
            ]);
        }

        if (! $deleted) {
            return redirect()->back()->with('error', 'No tempo processing data found to delete.');
        }

        return redirect()->back()->with('success', 'Tempo processing data deleted successfully.');
    }

    /**
     * Delete an active tempo processing task and cancel it in the microservice.
     */
    public function deleteTask(Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        if (! config('services.audio_analysis.enabled')) {
            return redirect()->back()->with('error', 'Audio processing is currently disabled.');
        }

        if (! $upload->tempoTask) {
            return redirect()->back()->with('error', 'No tempo processing task found to delete.');
        }

        if (! $upload->tempoTask->canBeDeleted()) {
            return redirect()->back()->with('error', 'This tempo processing task cannot be deleted in its current state.');
        }

        // Check service availability
        if (! $this->analysisService->isServiceAvailable()) {
            return redirect()->back()->with('error', 'Audio processing service is currently unavailable.');
        }

        /** @var \App\Models\UploadTempoTask $tempoTask */
        $tempoTask = $upload->tempoTask;
        $success = $this->analysisService->deleteTempoTask($tempoTask);

        if ($success) {
            Log::info('Tempo processing task deleted via user action', [
                'upload_id' => $upload->id,
                'task_id' => $upload->tempoTask->task_id,
                'user_id' => Auth::user()->id,
            ]);

            return redirect()->back()->with('success', 'Tempo processing task has been cancelled and deleted. You can now start new tempo processing.');
        } else {
            return redirect()->back()->with('warning', 'Tempo processing task was marked as deleted locally, but there may have been an issue communicating with the processing service.');
        }
    }

    /**
     * Get tempo processing presets (API endpoint).
     */
    public function presets(): JsonResponse
    {
        if (! config('services.audio_analysis.enabled')) {
            return response()->json([
                'error' => 'Audio processing is currently disabled.',
            ], 503);
        }

        $presets = $this->analysisService->getTempoPresets();

        return response()->json($presets);
    }

    /**
     * Get tempo processing suggestions for an upload (API endpoint).
     */
    public function suggestions(Upload $upload): JsonResponse
    {
        $this->authorize('view', $upload);

        if (! config('services.audio_analysis.enabled')) {
            return response()->json([
                'error' => 'Audio processing is currently disabled.',
            ], 503);
        }

        if (! $upload->analysis) {
            return response()->json([
                'error' => 'Upload must be analyzed before tempo suggestions can be generated.',
            ], 400);
        }

        $suggestions = $this->analysisService->getTempoSuggestions($upload);

        return response()->json($suggestions);
    }

    /**
     * Download a specific tempo processed file.
     */
    public function downloadTempo(Upload $upload, int $tempo): mixed
    {
        $this->authorize('view', $upload);

        $tempoRecord = $upload->tempos()->where('id', $tempo)->first();

        if (! $tempoRecord) {
            return redirect()->back()->with('error', 'Tempo processed file not found.');
        }

        Log::info('Tempo download requested', [
            'upload_id' => $upload->id,
            'tempo_id' => $tempo,
            'preset' => $tempoRecord->preset,
            'user_id' => Auth::user()->id,
        ]);

        // If stored on R2, redirect to R2 URL
        if ($tempoRecord->isStoredOnR2()) {
            $r2Url = config('filesystems.disks.r2.url').'/'.$tempoRecord->file_path;

            return redirect()->away($r2Url);
        }

        // If stored locally, serve the file from private storage
        $filePath = $tempoRecord->file_path;

        // Handle both old and new file path formats
        if (str_starts_with($filePath, 'private/')) {
            // New format: file_path already includes 'private/'
            $fullPath = storage_path('app/'.$filePath);
        } else {
            // Old format: file_path needs 'private/' prepended
            $fullPath = storage_path('app/private/'.$filePath);
        }

        if (! file_exists($fullPath)) {
            return redirect()->back()->with('error', 'Tempo processed file not found on disk.');
        }

        // Generate a descriptive filename
        $originalName = pathinfo($upload->filename, PATHINFO_FILENAME);
        $extension = pathinfo($fullPath, PATHINFO_EXTENSION);
        $presetName = str_replace('_', '-', $tempoRecord->preset);
        $downloadName = "{$originalName}-{$presetName}.{$extension}";

        return response()->download($fullPath, $downloadName);
    }
}
