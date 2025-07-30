<?php

namespace App\Http\Controllers;

use App\Http\Requests\StoreUploadRequest;
use App\Http\Requests\UpdateUploadRequest;
use App\Http\Resources\UploadResource;
use App\Models\Upload;
use Illuminate\Http\Request;
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
        $uploads = Auth::user()->uploads()->latest()->paginate(10);

        return inertia('Uploads/Index', [
            'uploads' => UploadResource::collection($uploads),
        ]);
    }

    /**
     * Show the form for creating a new upload.
     */
    public function create()
    {
        return inertia('Uploads/Create');
    }

    /**
     * Store a newly created upload in storage.
     */
    public function store(StoreUploadRequest $request)
    {
        $user = Auth::user();
        $file = $request->file('audio_file');
        $originalFilename = $file->getClientOriginalName();
        $extension = $file->getClientOriginalExtension();

        // Generate a unique filename
        $filename = Str::uuid() . '.' . $extension;

        // Store the original file in the private storage
        $path = $file->storeAs('uploads/original', $filename, 'private');

        // Create the upload record with pending status
        $upload = $user->uploads()->create([
            'title' => $request->input('title'),
            'description' => $request->input('description', ''),
            'filename' => $originalFilename,
            'path' => $path,
            'mime_type' => $file->getMimeType(),
            'size' => $file->getSize(),
            'status' => 'pending', // Set as pending since we need to process it
        ]);

        // Dispatch a job to process the audio file
        \App\Jobs\ProcessAudioUpload::dispatch($upload);

        return redirect()->route('uploads.index')
            ->with('success', 'Audio file uploaded successfully and is now being processed!');
    }

    /**
     * Display the specified upload.
     */
    public function show(Upload $upload)
    {
        $this->authorize('view', $upload);

        return inertia('Uploads/Show', [
            'upload' => new UploadResource($upload),
        ]);
    }

    /**
     * Show the form for editing the specified upload.
     */
    public function edit(Upload $upload)
    {
        $this->authorize('update', $upload);

        return inertia('Uploads/Edit', [
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

            return redirect()->route('uploads.edit', $upload)
                ->with('success', 'Upload details updated and the new audio file is processing!');
        }

        return redirect()->route('uploads.edit', $upload)
            ->with('success', 'Upload details updated successfully!');
    }

    /**
     * Remove the specified upload from storage.
     */
    public function destroy(Upload $upload)
    {
        $this->authorize('delete', $upload);

        // Delete the files from storage
        if (Storage::disk('private')->exists($upload->path)) {
            Storage::disk('private')->delete($upload->path);
        }

        if (Storage::disk('public')->exists($upload->stream_path)) {
            Storage::disk('public')->delete($upload->stream_path);
        }

        // Delete the database record
        $upload->delete();

        return redirect()->route('uploads.index')
            ->with('success', 'Upload deleted successfully!');
    }
}
