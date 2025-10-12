<?php

namespace App\Services;

use App\Models\Upload;
use App\Models\User;
use DateTimeInterface;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

/**
 * Class FileStorageService
 *
 * Consolidates file storage operations for uploads (local and R2).
 */
class FileStorageService
{
    /**
     * Store processed file (already client-processed) as stream file.
     *
     * @param  array<string,mixed>  $uploadData
     * @return array<string,mixed>
     */
    public function storeProcessedFile(UploadedFile $file, User $user, array $uploadData): array
    {
        try {
            $filename = Str::slug($uploadData['title']).'-'.Str::uuid().'.ogg';
            $disk = config('filesystems.default');
            $date = now();

            $streamPath = sprintf('uploads/stream/%s/%s/%s',
                $user->id,
                $date->format('Y/m/d'),
                $filename
            );

            if ($disk === 'r2') {
                // Store directly to public bucket since it's already processed
                $file->storeAs(
                    dirname($streamPath),
                    basename($streamPath),
                    'r2_public'
                );

                return array_merge($uploadData, [
                    'path' => $streamPath,
                    'stream_path' => $streamPath,
                    'uses_r2_storage' => true,
                ]);
            }

            // Local storage
            $file->storeAs(dirname($streamPath), basename($streamPath), 'public');

            return array_merge($uploadData, [
                'path' => $streamPath,
                'stream_path' => $streamPath,
                'uses_r2_storage' => false,
            ]);
        } catch (\Exception $e) {
            Log::error('FileStorageService::storeProcessedFile error: '.$e->getMessage(), [
                'user_id' => $user->id,
                'file' => $file->getClientOriginalName(),
            ]);

            return $uploadData;
        }
    }

    /**
     * Main file storage orchestrator.
     *
     * @param  array<string,mixed>  $uploadData
     * @return array<string,mixed>
     */
    public function storeFile(UploadedFile $file, User $user, array $uploadData): array
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
     * Main deletion orchestrator.
     */
    public function deleteUploadFiles(Upload $upload): void
    {
        $disk = config('filesystems.default');

        if ($disk === 'r2') {
            $this->deleteR2Files($upload);
        } else {
            $this->deleteLocalFiles($upload, $disk);
        }
    }

    /**
     * Handle R2 private bucket storage for original files.
     *
     * @param  array<string,mixed>  $uploadData
     * @return array<string,mixed>
     */
    private function storeFileToR2(UploadedFile $file, User $user, array $uploadData, string $filename, DateTimeInterface $date): array
    {
        try {
            $r2Path = 'uploads/'.$user->id.'/'.$date->format('Y/m/d');
            $file->storeAs($r2Path, $filename, 'r2_private');

            $fullR2Path = $r2Path.'/'.$filename;

            return array_merge($uploadData, [
                'r2_upload_path' => $fullR2Path,
                'uses_r2_storage' => true,
                'r2_uploaded_at' => now(),
                'path' => $fullR2Path,
            ]);
        } catch (\Exception $e) {
            Log::error('FileStorageService::storeFileToR2 error: '.$e->getMessage(), [
                'user_id' => $user->id,
                'file' => $file->getClientOriginalName(),
            ]);

            return $uploadData;
        }
    }

    /**
     * Handle local storage operations.
     *
     * @param  array<string,mixed>  $uploadData
     * @return array<string,mixed>
     */
    private function storeFileLocally(UploadedFile $file, User $user, array $uploadData, string $filename, DateTimeInterface $date, string $disk): array
    {
        try {
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
        } catch (\Exception $e) {
            Log::error('FileStorageService::storeFileLocally error: '.$e->getMessage(), [
                'user_id' => $user->id,
                'file' => $file->getClientOriginalName(),
            ]);

            return $uploadData;
        }
    }

    /**
     * Delete files from both R2 private and public buckets.
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
     * Delete individual files from R2 buckets.
     */
    private function deleteFromR2Bucket(?string $path, string $disk, ?string $warningMessage = null): void
    {
        if (! $path) {
            return;
        }

        try {
            if (Storage::disk($disk)->exists($path)) {
                Storage::disk($disk)->delete($path);
            } elseif ($warningMessage) {
                Log::warning($warningMessage);
            }
        } catch (\Exception $e) {
            Log::error('FileStorageService::deleteFromR2Bucket error: '.$e->getMessage(), [
                'path' => $path,
                'disk' => $disk,
            ]);
        }
    }

    /**
     * Delete local files from configured disk(s).
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