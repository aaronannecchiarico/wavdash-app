<?php

namespace App\Services;

use Exception;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class R2StorageService
{
    private string $disk = 'r2';

    /**
     * Check if R2 storage is enabled based on the default disk configuration.
     */
    public function isEnabled(): bool
    {
        return config('filesystems.default') === 'r2' &&
               ! empty(config('filesystems.disks.r2.key')) &&
               ! empty(config('filesystems.disks.r2.secret')) &&
               ! empty(config('filesystems.disks.r2.endpoint'));
    }

    /**
     * Upload a file to R2 storage with organized path structure.
     */
    public function uploadFile(UploadedFile $file, string $prefix = 'uploads', ?int $userId = null): ?string
    {
        if (! $this->isEnabled()) {
            return null;
        }

        try {
            // Create organized path: uploads/user_id/2024/01/15/uuid.ext
            $date = now();
            $uuid = Str::uuid();
            $extension = $file->getClientOriginalExtension();

            $path = sprintf(
                '%s/%s/%s/%s.%s',
                $prefix,
                $userId ? $userId : 'anonymous',
                $date->format('Y/m/d'),
                $uuid,
                $extension
            );

            // Upload to R2
            $success = Storage::disk($this->disk)->put($path, file_get_contents($file));

            if ($success) {
                Log::info('File uploaded to R2', ['path' => $path]);

                return $path;
            }

            Log::error('Failed to upload file to R2', ['path' => $path]);

            return null;

        } catch (Exception $e) {
            Log::error('R2 upload error: '.$e->getMessage(), [
                'file' => $file->getClientOriginalName(),
                'exception' => $e,
            ]);

            return null;
        }
    }

    /**
     * Upload file content to R2 storage.
     */
    public function uploadContent(string $content, string $path): bool
    {
        if (! $this->isEnabled()) {
            return false;
        }

        try {
            $success = Storage::disk($this->disk)->put($path, $content);

            if ($success) {
                Log::info('Content uploaded to R2', ['path' => $path]);

                return true;
            }

            Log::error('Failed to upload content to R2', ['path' => $path]);

            return false;

        } catch (Exception $e) {
            Log::error('R2 content upload error: '.$e->getMessage(), [
                'path' => $path,
                'exception' => $e,
            ]);

            return false;
        }
    }

    /**
     * Download a file from R2 storage.
     */
    public function getFile(string $path): ?string
    {
        if (! $this->isEnabled()) {
            return null;
        }

        try {
            if (Storage::disk($this->disk)->exists($path)) {
                return Storage::disk($this->disk)->get($path);
            }

            Log::warning('File not found in R2', ['path' => $path]);

            return null;

        } catch (Exception $e) {
            Log::error('R2 download error: '.$e->getMessage(), [
                'path' => $path,
                'exception' => $e,
            ]);

            return null;
        }
    }

    /**
     * Check if a file exists in R2 storage.
     */
    public function fileExists(string $path): bool
    {
        if (! $this->isEnabled()) {
            return false;
        }

        try {
            return Storage::disk($this->disk)->exists($path);
        } catch (Exception $e) {
            Log::error('R2 file exists check error: '.$e->getMessage(), [
                'path' => $path,
                'exception' => $e,
            ]);

            return false;
        }
    }

    /**
     * Delete a file from R2 storage.
     */
    public function deleteFile(string $path): bool
    {
        if (! $this->isEnabled()) {
            return false;
        }

        try {
            if (Storage::disk($this->disk)->exists($path)) {
                $success = Storage::disk($this->disk)->delete($path);

                if ($success) {
                    Log::info('File deleted from R2', ['path' => $path]);

                    return true;
                }
            }

            Log::warning('File not found or failed to delete from R2', ['path' => $path]);

            return false;

        } catch (Exception $e) {
            Log::error('R2 delete error: '.$e->getMessage(), [
                'path' => $path,
                'exception' => $e,
            ]);

            return false;
        }
    }

    /**
     * Get the public URL for an R2 file.
     */
    public function getPublicUrl(string $path): ?string
    {
        $publicUrl = config('filesystems.disks.r2.url');

        if (empty($publicUrl)) {
            return null;
        }

        return rtrim($publicUrl, '/').'/'.ltrim($path, '/');
    }

    /**
     * Upload multiple files (like stems) to R2 with organized paths.
     *
     * @param  array<string, string>  $stemFiles
     * @return array<string, string>
     */
    public function uploadStems(array $stemFiles, string $basePath): array
    {
        if (! $this->isEnabled()) {
            return [];
        }

        $uploadedStems = [];

        foreach ($stemFiles as $stemName => $filePath) {
            try {
                $r2Path = sprintf('stems/%s/%s.wav', $basePath, $stemName);

                if (file_exists($filePath)) {
                    $content = file_get_contents($filePath);
                    $success = Storage::disk($this->disk)->put($r2Path, $content);

                    if ($success) {
                        $uploadedStems[$stemName] = $r2Path;
                        Log::info('Stem uploaded to R2', [
                            'stem' => $stemName,
                            'path' => $r2Path,
                        ]);
                    }
                }
            } catch (Exception $e) {
                Log::error('Failed to upload stem to R2: '.$e->getMessage(), [
                    'stem' => $stemName,
                    'path' => $filePath,
                    'exception' => $e,
                ]);
            }
        }

        return $uploadedStems;
    }

    /**
     * Get storage information and statistics.
     *
     * @return array{enabled: bool, disk: string, bucket: mixed, endpoint: mixed, public_url: mixed}
     */
    public function getStorageInfo(): array
    {
        return [
            'enabled' => $this->isEnabled(),
            'disk' => $this->disk,
            'bucket' => config('filesystems.disks.r2.bucket'),
            'endpoint' => config('filesystems.disks.r2.endpoint'),
            'public_url' => config('filesystems.disks.r2.url'),
        ];
    }

    /**
     * Copy a file from local storage to R2.
     */
    public function copyFromLocal(string $localPath, string $r2Path): bool
    {
        if (! $this->isEnabled() || ! file_exists($localPath)) {
            return false;
        }

        try {
            $content = file_get_contents($localPath);

            return $this->uploadContent($content, $r2Path);
        } catch (Exception $e) {
            Log::error('Failed to copy file from local to R2: '.$e->getMessage(), [
                'local_path' => $localPath,
                'r2_path' => $r2Path,
                'exception' => $e,
            ]);

            return false;
        }
    }

    /**
     * Migrate existing upload to R2 storage.
     */
    public function migrateUpload(\App\Models\Upload $upload): bool
    {
        if (! $this->isEnabled() || $upload->usesR2Storage()) {
            return false;
        }

        try {
            // Check if local file exists
            $localPath = storage_path('app/'.$upload->path);
            if (! file_exists($localPath)) {
                Log::warning('Local file not found for migration', [
                    'upload_id' => $upload->id,
                    'path' => $localPath,
                ]);

                return false;
            }

            // Generate R2 path with user organization
            $date = $upload->created_at;
            $extension = pathinfo($upload->filename, PATHINFO_EXTENSION);
            $r2Path = sprintf(
                'uploads/%s/%s/%s.%s',
                $upload->user_id,
                $date->format('Y/m/d'),
                Str::uuid(),
                $extension
            );

            // Copy to R2
            if ($this->copyFromLocal($localPath, $r2Path)) {
                // Update upload record
                $upload->update([
                    'r2_upload_path' => $r2Path,
                    'uses_r2_storage' => true,
                    'r2_uploaded_at' => now(),
                ]);

                Log::info('Upload migrated to R2', [
                    'upload_id' => $upload->id,
                    'r2_path' => $r2Path,
                ]);

                return true;
            }

            return false;

        } catch (Exception $e) {
            Log::error('Failed to migrate upload to R2: '.$e->getMessage(), [
                'upload_id' => $upload->id,
                'exception' => $e,
            ]);

            return false;
        }
    }
}
