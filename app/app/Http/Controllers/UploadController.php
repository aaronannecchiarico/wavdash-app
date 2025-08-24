<?php

namespace App\Http\Controllers;

use App\Http\Requests\StoreUploadRequest;
use App\Http\Requests\UpdateUploadRequest;
use App\Http\Resources\UploadResource;
use App\Models\Upload;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class UploadController extends Controller
{
    /**
     * Display a listing of the user's uploads.
     */
    public function index(Request $request)
    {
        $query = Auth::user()->uploads();

        // Filtering by basic properties
        if ($request->has('status')) {
            $query->where('status', $request->input('status'));
        }
        if ($request->has('type')) {
            $query->where('mime_type', 'like', 'audio/'.$request->input('type'));
        }

        // Filtering by processing status
        if ($request->has('analysis_status')) {
            $analysisStatus = $request->input('analysis_status');
            if ($analysisStatus === 'completed') {
                $query->whereHas('analysis');
            } elseif ($analysisStatus === 'not_completed') {
                $query->whereDoesntHave('analysis');
            } elseif ($analysisStatus === 'in_progress') {
                $query->whereHas('analysisTask', function ($q) {
                    $q->whereIn('status', ['pending', 'processing']);
                });
            }
        }

        if ($request->has('stems_status')) {
            $stemsStatus = $request->input('stems_status');
            if ($stemsStatus === 'completed') {
                $query->whereHas('stems');
            } elseif ($stemsStatus === 'not_completed') {
                $query->whereDoesntHave('stems');
            } elseif ($stemsStatus === 'in_progress') {
                $query->whereHas('stemTask', function ($q) {
                    $q->whereIn('status', ['pending', 'processing']);
                });
            }
        }

        if ($request->has('tempo_status')) {
            $tempoStatus = $request->input('tempo_status');
            if ($tempoStatus === 'completed') {
                $query->whereHas('tempos');
            } elseif ($tempoStatus === 'not_completed') {
                $query->whereDoesntHave('tempos');
            } elseif ($tempoStatus === 'in_progress') {
                $query->whereHas('tempoTask', function ($q) {
                    $q->whereIn('status', ['pending', 'processing']);
                });
            }
        }

        // Sorting
        $sort = $request->input('sort', 'updated_at');
        $direction = $request->input('direction', 'desc');
        if (in_array($sort, ['title', 'size', 'duration', 'updated_at'])) {
            $query->orderBy($sort, $direction);
        } else {
            $query->latest('updated_at');
        }

        $uploads = $query->with(['analysisTask', 'analysis', 'stemTask', 'stems', 'tempoTask', 'tempos'])->paginate(10)->withQueryString();

        $statuses = Upload::distinct()->pluck('status')->toArray();
        $types = Upload::distinct()->pluck('mime_type')->map(function ($mime) {
            return explode('/', $mime)[1];
        })->unique()->toArray();

        return inertia('uploads/index', [
            'uploads' => UploadResource::collection($uploads),
            'filters' => $request->only(['sort', 'direction', 'status', 'type', 'analysis_status', 'stems_status', 'tempo_status']),
            'filterOptions' => [
                'statuses' => $statuses,
                'types' => $types,
                'processingStatuses' => [
                    'completed' => 'Completed',
                    'not_completed' => 'Not Completed',
                    'in_progress' => 'In Progress',
                ],
            ],
        ]);
    }

    /**
     * API endpoint for fetching uploads (for dialogs, etc.)
     */
    public function apiIndex(Request $request)
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
    public function create()
    {
        return inertia('uploads/create');
    }

    /**
     * Store a newly created upload in storage.
     */
    public function store(StoreUploadRequest $request)
    {
        $user = Auth::user();
        $file = $request->file('audio_file');

        $uploadData = $this->prepareUploadData($request, $file);
        $this->logUploadStart($user, $file, $uploadData);

        $uploadData = $this->storeFile($file, $user, $uploadData);
        $upload = $this->createUploadRecord($user, $uploadData);
        $this->dispatchProcessingJob($upload);

        $this->logUploadSuccess($upload);

        return redirect()->route('uploads.index')
            ->with('success', 'Audio file uploaded successfully and is now being processed!');
    }

    /**
     * Display the specified upload.
     */
    public function show(Upload $upload)
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
    public function edit(Upload $upload)
    {
        $this->authorize('update', $upload);

        return inertia('uploads/edit', [
            'upload' => new UploadResource($upload),
        ]);
    }

    /**
     * Update the specified upload in storage.
     */
    public function update(UpdateUploadRequest $request, Upload $upload)
    {
        $this->authorize('update', $upload);

        $upload->update($request->only('title', 'description'));

        if ($request->hasFile('audio_file')) {
            // Delete the old files from storage
            if (Storage::disk('private')->exists($upload->path)) {
                Storage::disk('private')->delete($upload->path);
            }
            if ($upload->stream_path && Storage::disk('public')->exists($upload->stream_path)) {
                Storage::disk('public')->delete($upload->stream_path);
            }

            $file = $request->file('audio_file');
            $originalFilename = $file->getClientOriginalName();
            $extension = $file->getClientOriginalExtension();
            $filename = Str::uuid().'.'.$extension;
            $path = $file->storeAs('uploads/original', $filename, 'private');

            $upload->update([
                'filename' => $originalFilename,
                'path' => $path,
                'mime_type' => $file->getMimeType(),
                'size' => $file->getSize(),
                'status' => 'pending',
                'stream_path' => null,
                'duration' => null,
            ]);

            \App\Jobs\ProcessAudioUpload::dispatch($upload);

            return redirect()->route('uploads.index', $upload)
                ->with('success', 'Upload details updated and the new audio file is processing!');
        }

        return redirect()->route('uploads.index', $upload)
            ->with('success', 'Upload details updated successfully!');
    }

    /**
     * Remove the specified upload from storage.
     */
    public function destroy(Upload $upload)
    {
        try {
            $this->authorize('delete', $upload);
            $title = $upload->title;

            $this->deleteUploadFiles($upload);
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
     */
    private function prepareUploadData(StoreUploadRequest $request, $file): array
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
     */
    private function logUploadStart($user, $file, array $uploadData): void
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
     */
    private function storeFile($file, $user, array $uploadData): array
    {
        $filename = Str::uuid().'.'.$file->getClientOriginalExtension();
        $disk = config('filesystems.default');
        $date = now();

        if ($disk === 'r2') {
            return $this->storeFileToR2($file, $user, $uploadData, $filename, $date);
        }

        return $this->storeFileLocally($file, $user, $uploadData, $filename, $date, $disk);
    }

    /**
     * Store file to R2 private bucket.
     */
    private function storeFileToR2($file, $user, array $uploadData, string $filename, $date): array
    {
        $r2Path = 'uploads/'.$user->id.'/'.$date->format('Y/m/d');
        $file->storeAs($r2Path, $filename, 'r2_private');

        $fullR2Path = $r2Path.'/'.$filename;

        return array_merge($uploadData, [
            'r2_upload_path' => $fullR2Path,
            'uses_r2_storage' => true,
            'r2_uploaded_at' => now(),
            'path' => $fullR2Path,
        ]);
    }

    /**
     * Store file locally.
     */
    private function storeFileLocally($file, $user, array $uploadData, string $filename, $date, string $disk): array
    {
        $storageDisk = $disk === 'local' ? 'private' : $disk;
        $directory = 'uploads/'.$user->id.'/'.$date->format('Y/m/d');
        $path = sprintf(
            'uploads/%s/%s/%s',
            $user->id,
            $date->format('Y/m/d'),
            $filename
        );

        $file->storeAs($directory, $filename, $storageDisk);

        return array_merge($uploadData, [
            'path' => $path,
            'uses_r2_storage' => false,
        ]);
    }

    /**
     * Create upload record.
     */
    private function createUploadRecord($user, array $uploadData): Upload
    {
        return $user->uploads()->create($uploadData);
    }

    /**
     * Dispatch audio processing job.
     */
    private function dispatchProcessingJob(Upload $upload): void
    {
        \App\Jobs\ProcessAudioUpload::dispatch($upload);
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
     * Delete all files associated with upload.
     */
    private function deleteUploadFiles(Upload $upload): void
    {
        $disk = config('filesystems.default');

        if ($upload->usesR2Storage() && $disk === 'r2') {
            $this->deleteR2Files($upload);
        } else {
            $this->deleteLocalFiles($upload, $disk);
        }
    }

    /**
     * Delete R2 files from both private and public buckets.
     */
    private function deleteR2Files(Upload $upload): void
    {
        // Delete from private bucket
        $this->deleteFromR2Bucket($upload->r2_upload_path, 'r2_private', "R2 private file not found for upload ID: {$upload->id}");
        $this->deleteFromR2Bucket($upload->r2_analysis_path, 'r2_private', "R2 analysis file not found for upload ID: {$upload->id}");

        // Delete stems from private bucket
        if ($upload->hasR2Stems()) {
            foreach ($upload->r2_stems_paths as $stemPath) {
                $this->deleteFromR2Bucket($stemPath, 'r2_private');
            }
        }

        // Delete from public bucket
        $this->deleteFromR2Bucket($upload->stream_path, 'r2_public', "R2 public stream file not found for upload ID: {$upload->id}");

        // Delete public stems
        if ($upload->hasR2Stems()) {
            foreach ($upload->r2_stems_paths as $stemPath) {
                $this->deleteFromR2Bucket($stemPath, 'r2_public');
            }
        }
    }

    /**
     * Delete file from R2 bucket.
     */
    private function deleteFromR2Bucket(?string $path, string $disk, ?string $warningMessage = null): void
    {
        if (! $path) {
            return;
        }

        if (Storage::disk($disk)->exists($path)) {
            Storage::disk($disk)->delete($path);
        } elseif ($warningMessage) {
            Log::warning($warningMessage);
        }
    }

    /**
     * Delete local files.
     */
    private function deleteLocalFiles(Upload $upload, string $disk): void
    {
        $storageDisk = $disk === 'local' ? 'private' : $disk;

        Log::info('Deleting local files for upload', [
            'upload_id' => $upload->id,
            'storage_disk' => $storageDisk,
            'original_path' => $upload->path,
            'stream_path' => $upload->stream_path,
        ]);

        // Delete original file
        if ($upload->path && Storage::disk($storageDisk)->exists($upload->path)) {
            Storage::disk($storageDisk)->delete($upload->path);
            Log::info('Deleted original file', ['path' => $upload->path]);
        } elseif ($upload->path) {
            Log::warning("Original file not found for upload ID: {$upload->id}", [
                'path' => $upload->path,
                'disk' => $storageDisk,
            ]);
        }

        // Delete stream file
        if ($upload->stream_path && Storage::disk('public')->exists($upload->stream_path)) {
            Storage::disk('public')->delete($upload->stream_path);
            Log::info('Deleted stream file', ['path' => $upload->stream_path]);
        } elseif ($upload->stream_path) {
            Log::warning("Stream file not found for upload ID: {$upload->id}", [
                'stream_path' => $upload->stream_path,
            ]);
        }
    }
}
