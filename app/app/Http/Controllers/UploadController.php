<?php

namespace App\Http\Controllers;

use App\Events\UploadProcessed;
use App\Http\Requests\StoreUploadRequest;
use App\Http\Requests\UpdateUploadRequest;
use App\Http\Resources\UploadResource;
use App\Models\Upload;
use App\Models\User;
use App\Services\AudioProcessingService;
use App\Services\FileStorageService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Inertia\Response as InertiaResponse;

class UploadController extends Controller
{
    public function __construct(
        private AudioProcessingService $audioProcessingService,
        private FileStorageService $fileStorageService
    ) {}

    /**
     * Display a listing of the user's uploads.
     *
     * @param  Request  $request  The current HTTP request containing filters and sorting options.
     * @return InertiaResponse An Inertia response with paginated uploads and filter options.
     */
    public function index(Request $request): InertiaResponse
    {
        $user = Auth::user();
        if (! $user instanceof User) {
            abort(401);
        }

        $query = $user->uploads()
            ->when($request->filled('status'),
                fn ($q) => $q->where('status', $request->input('status')))
            ->when($request->filled('type'),
                fn ($q) => $q->where('mime_type', 'like', 'audio/'.$request->input('type')))
            ->when($request->filled('analysis_status'),
                fn ($q) => $q->withAnalysisStatus($request->input('analysis_status')))
            ->when($request->filled('stems_status'),
                fn ($q) => $q->withStemsStatus($request->input('stems_status')))
            ->when($request->filled('tempo_status'),
                fn ($q) => $q->withTempoStatus($request->input('tempo_status')))
            ->userSort(
                $request->input('sort', 'updated_at'),
                $request->input('direction', 'desc')
            );

        $uploads = $query->with([
            'analysisTask', 'analysis', 'stemTask', 'stems', 'tempoTask', 'tempos',
        ])->paginate(10)->withQueryString();

        return inertia('uploads/index', [
            'uploads' => UploadResource::collection($uploads),
            'filters' => $request->only([
                'sort', 'direction', 'status', 'type',
                'analysis_status', 'stems_status', 'tempo_status',
            ]),
            'filterOptions' => $this->getFilterOptions(),
        ]);
    }

    /**
     * API endpoint for fetching uploads (for dialogs, etc.)
     */
    public function apiIndex(Request $request): JsonResponse
    {
        $query = $request->user()->uploads();

        if ($request->filled('search')) {
            $search = $request->input('search');
            $query->where(function ($q) use ($search) {
                $q->where('title', 'like', "%{$search}%")
                    ->orWhere('filename', 'like', "%{$search}%")
                    ->orWhere('description', 'like', "%{$search}%");
            });
        }

        $uploads = $query->latest()
            ->limit($request->integer('limit', 20))
            ->with(['analysis', 'stems'])
            ->get();

        // Add computed properties for the frontend
        $uploads = $uploads->map(function ($upload) {
            return [
                'id' => $upload->id,
                'title' => $upload->title,
                'filename' => $upload->filename,
                'description' => $upload->description,
                'status' => $upload->status,
                'created_at' => $upload->created_at,
                'has_stems' => $upload->hasStems(),
                'has_analysis' => $upload->hasAnalysis(),
            ];
        });

        return response()->json([
            'uploads' => $uploads,
        ]);
    }

    /**
     * Show the form for creating a new upload.
     */
    public function create(): InertiaResponse
    {
        return inertia('uploads/create', [
            'audioProcessingConfig' => $this->audioProcessingService->getFrontendConfig(),
        ]);
    }

    /**
     * Store a newly created upload in storage.
     *
     * @throws \Throwable
     */
    public function store(StoreUploadRequest $request): RedirectResponse
    {
        $startTime = microtime(true);
        $user = Auth::user();
        if (! $user instanceof User) {
            abort(401);
        }
        $file = $request->file('audio_file');
        $isClientProcessed = $request->boolean('client_processed', false);

        // Phase 4: Client-side processing is now required for all uploads
        if (! $isClientProcessed) {
            return back()->withErrors([
                'audio_file' => 'Audio processing failed. Please try uploading again with a supported browser.',
            ]);
        }

        $processingTime = $request->input('processing_time_ms');
        $originalSize = $request->input('original_size');
        $processedSize = $file->getSize();

        $this->audioProcessingService->logPerformanceMetrics([
            'processing_type' => 'client',
            'client_processing_time_ms' => $processingTime,
            'original_file_size' => $originalSize,
            'processed_file_size' => $processedSize,
            'compression_ratio' => $originalSize > 0 ? round($processedSize / $originalSize, 2) : 0,
            'file_format' => $file->getMimeType(),
        ]);

        return $this->storeClientProcessedUpload($request, $user, $file, $startTime);
    }

    /**
     * Store client-processed upload directly as ready.
     *
     * @param  float  $startTime  Timestamp when upload started (microtime)
     */
    private function storeClientProcessedUpload(StoreUploadRequest $request, User $user, UploadedFile $file, float $startTime): RedirectResponse
    {
        $uploadData = [
            'title' => $request->input('title'),
            'description' => $request->input('description', ''),
            'filename' => $request->input('original_filename', $file->getClientOriginalName()),
            'mime_type' => 'audio/ogg', // Client always processes to OGG
            'size' => $request->input('original_size', $file->getSize()),
            'status' => 'ready', // Skip processing queue
            'duration_seconds' => $request->input('duration'),
        ];

        $this->logUploadStart($user, $file, $uploadData);

        // Store the pre-processed OGG file directly as stream file
        $uploadData = $this->fileStorageService->storeProcessedFile($file, $user, $uploadData);
        $upload = $this->createUploadRecord($user, $uploadData);

        // Broadcast ready event immediately
        UploadProcessed::dispatch($upload);

        $totalTime = (microtime(true) - $startTime) * 1000;

        $this->audioProcessingService->logProcessingSuccess([
            'processing_type' => 'client',
            'total_time_ms' => $totalTime,
            'upload_id' => $upload->id,
            'final_status' => 'ready',
        ]);

        $this->logUploadSuccess($upload);

        return redirect()->route('uploads.index')
            ->with('success', 'Audio file uploaded and processed successfully!');
    }

    /**
     * Store pre-processed file directly to stream storage.
     *
     * @param  UploadedFile  $file
     * @param  User  $user
     * @param  array<string, mixed>  $uploadData
     * @return array<string, mixed>
     */

    /**
     * Display the specified upload.
     */
    public function show(Upload $upload): InertiaResponse
    {
        $this->authorize('view', $upload);

        $upload->load(['analysisTask', 'analysis', 'stemTask', 'stems', 'tempoTask', 'tempos']);

        return inertia('uploads/show', [
            'upload' => new UploadResource($upload),
        ]);
    }

    /**
     * Show the form for editing the specified upload.
     */
    public function edit(Upload $upload): InertiaResponse
    {
        $this->authorize('update', $upload);

        return inertia('uploads/edit', [
            'upload' => new UploadResource($upload),
        ]);
    }

    /**
     * Update the specified upload in storage.
     */
    public function update(UpdateUploadRequest $request, Upload $upload): RedirectResponse
    {
        $this->authorize('update', $upload);

        if ($request->hasFile('audio_file')) {
            // Phase 4: Audio file updates are no longer supported via server-side processing
            // Users must create a new upload with client-side processing
            return back()->withErrors([
                'audio_file' => 'Audio file updates are no longer supported. Please create a new upload instead.',
            ]);
        }

        $upload->update($request->only('title', 'description'));

        return redirect()->route('uploads.show', $upload)
            ->with('success', 'Upload details updated successfully!');
    }

    /**
     * Remove the specified upload from storage.
     */
    public function destroy(Upload $upload): RedirectResponse
    {
        try {
            $this->authorize('delete', $upload);
            $title = $upload->title;

            $this->fileStorageService->deleteUploadFiles($upload);
            $upload->delete();

            return redirect()->route('uploads.index')
                ->with('success', "\"$title\" was deleted successfully!");
        } catch (\Exception $e) {
            Log::error("Error deleting upload ID {$upload->id}: ".$e->getMessage());

            return redirect()->route('uploads.index')
                ->with('error', 'Failed to delete the upload. '.$e->getMessage());
        }
    }

    /**
     * Prepare upload data from request and file.
     *
     * @return array<string, mixed>
     */
    private function prepareUploadData(StoreUploadRequest $request, UploadedFile $file): array
    {
        return [
            'title' => $request->input('title'),
            'description' => $request->input('description', ''),
            'filename' => $file->getClientOriginalName(),
            'mime_type' => $file->getMimeType(),
            'size' => $file->getSize(),
            'status' => 'pending',
        ];
    }

    /**
     * Log upload start information.
     *
     * @param  array<string, mixed>  $uploadData
     */
    private function logUploadStart(User $user, UploadedFile $file, array $uploadData): void
    {
        Log::info('Upload Controller - Starting file upload', [
            'user_id' => $user->id,
            'original_filename' => $uploadData['filename'],
            'configured_disk' => config('filesystems.default'),
            'file_size' => $file->getSize(),
            'file_mime' => $file->getMimeType(),
        ]);
    }

    /**
     * Store file based on configured disk.
     *
     * @param  UploadedFile  $file
     * @param  array<string, mixed>  $uploadData
     * @return array<string, mixed>
     */

    /**
     * Create upload record.
     *
     * @param  array<string, mixed>  $uploadData
     */
    private function createUploadRecord(User $user, array $uploadData): Upload
    {
        return $user->uploads()->create($uploadData);
    }

    /**
     * Log upload success.
     */
    private function logUploadSuccess(Upload $upload): void
    {
        Log::info('Upload created', [
            'id' => $upload->id,
            'storage' => config('filesystems.default'),
        ]);
    }

    /**
     * Get filter options for the upload index page.
     *
     * @return array<string, mixed>
     */
    private function getFilterOptions(): array
    {
        return [
            'statuses' => Upload::distinct()->pluck('status')->toArray(),
            'types' => Upload::distinct()->pluck('mime_type')
                ->map(fn ($mime) => explode('/', $mime)[1])
                ->unique()
                ->toArray(),
            'processingStatuses' => [
                'completed' => 'Completed',
                'not_completed' => 'Not Completed',
                'in_progress' => 'In Progress',
            ],
        ];
    }

    /**
     * Delete all files associated with upload.
     *
     * @param  Upload  $upload
     * @return void
     */
}
