<?php

namespace App\Http\Controllers;

use App\Http\Requests\StoreUploadRequest;
use App\Http\Requests\UpdateUploadRequest;
use App\Http\Resources\UploadResource;
use App\Models\Upload;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Str;

class UploadController extends Controller
{
    /**
     * Display a listing of the user's uploads.
     */
    public function index(Request $request)
    {
        $query = Auth::user()->uploads();

        // Filtering
        if ($request->has('status')) {
            $query->where('status', $request->input('status'));
        }
        if ($request->has('type')) {
            $query->where('mime_type', 'like', 'audio/' . $request->input('type'));
        }

        // Sorting
        $sort = $request->input('sort', 'updated_at');
        $direction = $request->input('direction', 'desc');
        if (in_array($sort, ['title', 'size', 'duration', 'updated_at'])) {
            $query->orderBy($sort, $direction);
        } else {
            $query->latest('updated_at');
        }

        $uploads = $query->with(['analysisTask', 'analysis'])->paginate(10)->withQueryString();

        $statuses = Upload::distinct()->pluck('status')->toArray();
        $types = Upload::distinct()->pluck('mime_type')->map(function ($mime) {
            return explode('/', $mime)[1];
        })->unique()->toArray();

        return inertia('uploads/index', [
            'uploads' => UploadResource::collection($uploads),
            'filters' => $request->only(['sort', 'direction', 'status', 'type']),
            'filterOptions' => [
                'statuses' => $statuses,
                'types' => $types,
            ],
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
        $originalFilename = $file->getClientOriginalName();

        $uploadData = [
            'title' => $request->input('title'),
            'description' => $request->input('description', ''),
            'filename' => $originalFilename,
            'mime_type' => $file->getMimeType(),
            'size' => $file->getSize(),
            'status' => 'pending',
        ];

        // Store file using the configured default disk with user-organized structure
        $filename = Str::uuid() . '.' . $file->getClientOriginalExtension();
        $disk = config('filesystems.default');
        $date = now();
        $path = sprintf(
            'uploads/%s/%s/%s',
            $user->id,
            $date->format('Y/m/d'),
            $filename
        );
        
        Log::info("Upload Controller - Starting file upload", [
            'user_id' => $user->id,
            'original_filename' => $originalFilename,
            'generated_filename' => $filename,
            'configured_disk' => $disk,
            'target_path' => $path,
            'file_size' => $file->getSize(),
            'file_mime' => $file->getMimeType()
        ]);
        
        if ($disk === 'r2') {
            // For R2 storage
            $file->storeAs('uploads/' . $user->id . '/' . $date->format('Y/m/d'), $filename, $disk);
            
            $uploadData = array_merge($uploadData, [
                'r2_upload_path' => $path,
                'uses_r2_storage' => true,
                'r2_uploaded_at' => now(),
                'path' => $path,
            ]);
            
            Log::info("File uploaded to R2", [
                'filename' => $originalFilename,
                'path' => $path
            ]);
        } else {
            // For local storage (or any other disk) - use same path structure
            $storageDisk = $disk === 'local' ? 'private' : $disk;
            $directory = 'uploads/' . $user->id . '/' . $date->format('Y/m/d');
            
            Log::info("Upload Controller - Storing to local disk", [
                'storage_disk' => $storageDisk,
                'directory' => $directory,
                'filename' => $filename,
                'full_path' => $path
            ]);
            
            $storedPath = $file->storeAs($directory, $filename, $storageDisk);
            $uploadData['path'] = $path;
            $uploadData['uses_r2_storage'] = false;
            
            Log::info("Upload Controller - File stored successfully", [
                'original_filename' => $originalFilename,
                'stored_path' => $storedPath,
                'upload_data_path' => $path,
                'storage_disk' => $storageDisk,
                'absolute_path' => Storage::disk($storageDisk)->path($path)
            ]);
        }

        // Create the upload record with pending status
        $upload = $user->uploads()->create($uploadData);

        // Dispatch a job to process the audio file
        \App\Jobs\ProcessAudioUpload::dispatch($upload);

        Log::info("Upload created", [
            'id' => $upload->id,
            'storage' => $disk
        ]);

        return redirect()->route('uploads.index')
            ->with('success', 'Audio file uploaded successfully and is now being processed!');
    }

    /**
     * Display the specified upload.
     */
    public function show(Upload $upload)
    {
        $this->authorize('view', $upload);

        $upload->load(['analysisTask', 'analysis']);

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
            $filename = Str::uuid() . '.' . $extension;
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

            // Store title for message
            $title = $upload->title;

            // Delete files based on storage configuration
            $disk = config('filesystems.default');
            
            if ($upload->usesR2Storage() && $disk === 'r2') {
                // Delete from R2 storage
                if ($upload->r2_upload_path && Storage::disk('r2')->exists($upload->r2_upload_path)) {
                    Storage::disk('r2')->delete($upload->r2_upload_path);
                } else {
                    Log::warning("R2 file not found for upload ID: {$upload->id}");
                }
                
                // Delete R2 stems if they exist
                if ($upload->hasR2Stems()) {
                    foreach ($upload->r2_stems_paths as $stemPath) {
                        if (Storage::disk('r2')->exists($stemPath)) {
                            Storage::disk('r2')->delete($stemPath);
                        }
                    }
                }
                
                // Delete R2 analysis file if it exists
                if ($upload->r2_analysis_path && Storage::disk('r2')->exists($upload->r2_analysis_path)) {
                    Storage::disk('r2')->delete($upload->r2_analysis_path);
                }
            } else {
                // Delete from local/private storage
                $storageDisk = $disk === 'local' ? 'private' : $disk;
                
                Log::info("Deleting local files for upload", [
                    'upload_id' => $upload->id,
                    'storage_disk' => $storageDisk,
                    'original_path' => $upload->path,
                    'stream_path' => $upload->stream_path
                ]);
                
                if ($upload->path && Storage::disk($storageDisk)->exists($upload->path)) {
                    Storage::disk($storageDisk)->delete($upload->path);
                    Log::info("Deleted original file", ['path' => $upload->path]);
                } else {
                    Log::warning("Original file not found for upload ID: {$upload->id}", [
                        'path' => $upload->path,
                        'disk' => $storageDisk,
                        'file_exists' => $upload->path ? Storage::disk($storageDisk)->exists($upload->path) : false
                    ]);
                }

                if ($upload->stream_path && Storage::disk('public')->exists($upload->stream_path)) {
                    Storage::disk('public')->delete($upload->stream_path);
                    Log::info("Deleted stream file", ['path' => $upload->stream_path]);
                } else if ($upload->stream_path) {
                    Log::warning("Stream file not found for upload ID: {$upload->id}", [
                        'stream_path' => $upload->stream_path,
                        'file_exists' => Storage::disk('public')->exists($upload->stream_path)
                    ]);
                }
            }

            $upload->delete();

            return redirect()->route('uploads.index')
                ->with('success', "\"$title\" was deleted successfully!");
        } catch (\Exception $e) {
            Log::error("Error deleting upload ID {$upload->id}: " . $e->getMessage());

            return redirect()->route('uploads.index')
                ->with('error', 'Failed to delete the upload. ' . $e->getMessage());
        }
    }
}
