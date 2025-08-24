<?php

namespace App\Services;

use App\Models\Upload;
use FFMpeg\Format\Audio\Vorbis;
use Illuminate\Filesystem\FilesystemAdapter;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use League\Flysystem\Filesystem;
use League\Flysystem\Local\LocalFilesystemAdapter;
use ProtoneMedia\LaravelFFMpeg\Support\FFMpeg;

class AudioConversionService
{
    /**
     * Convert audio file to OGG format and copy to public bucket/directory.
     */
    public function convertAndPublishAudio(
        Upload $upload,
        string $sourceFilePath,
        string $publicFilePath,
        string $fileType = 'stem'
    ): ?string {
        Log::info('AudioConversionService - Starting audio conversion', [
            'upload_id' => $upload->id,
            'source_path' => $sourceFilePath,
            'public_path' => $publicFilePath,
            'file_type' => $fileType,
            'uses_r2_storage' => $upload->usesR2Storage(),
        ]);

        try {
            if ($upload->usesR2Storage()) {
                return $this->convertAndPublishR2Audio($upload, $sourceFilePath, $publicFilePath, $fileType);
            }

            return $this->convertAndPublishLocalAudio($upload, $sourceFilePath, $publicFilePath, $fileType);

        } catch (\Exception $e) {
            Log::error('AudioConversionService - Conversion failed', [
                'upload_id' => $upload->id,
                'source_path' => $sourceFilePath,
                'public_path' => $publicFilePath,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            throw $e;
        }
    }

    /**
     * Convert and publish R2 audio file.
     */
    private function convertAndPublishR2Audio(
        Upload $upload,
        string $sourceFilePath,
        string $publicFilePath,
        string $fileType
    ): string {
        // Download source file from R2 to temp
        $tempSourcePath = $this->downloadFromR2ToTemp($upload, $sourceFilePath);

        if (! $tempSourcePath) {
            throw new \Exception("Failed to download source file from R2: {$sourceFilePath}");
        }

        try {
            // Convert to OGG in temp directory
            $convertedTempPath = $this->convertToOggInTemp($tempSourcePath, $publicFilePath);

            // Generate OGG public path
            $oggPublicPath = $this->replaceFileExtensionWithOgg($publicFilePath);

            // Upload converted file to R2 public bucket
            $content = file_get_contents($convertedTempPath);
            if (! Storage::disk('r2_public')->put($oggPublicPath, $content)) {
                throw new \Exception("Failed to upload converted file to R2 public bucket: {$oggPublicPath}");
            }

            Log::info('AudioConversionService - R2 conversion completed', [
                'upload_id' => $upload->id,
                'public_path' => $oggPublicPath,
                'file_type' => $fileType,
                'file_size' => strlen($content),
            ]);

            // Cleanup temp files
            if (file_exists($convertedTempPath)) {
                unlink($convertedTempPath);
            }

            return $oggPublicPath;

        } finally {
            // Cleanup source temp file
            if (file_exists($tempSourcePath)) {
                unlink($tempSourcePath);
            }
        }
    }

    /**
     * Convert and publish local audio file.
     */
    private function convertAndPublishLocalAudio(
        Upload $upload,
        string $sourceFilePath,
        string $publicFilePath,
        string $fileType
    ): string {
        // Convert source file directly to public directory
        $oggPublicPath = $this->convertLocalFileToPublic($sourceFilePath, $publicFilePath);

        Log::info('AudioConversionService - Local conversion completed', [
            'upload_id' => $upload->id,
            'source_path' => $sourceFilePath,
            'public_path' => $oggPublicPath,
            'file_type' => $fileType,
            'file_exists' => Storage::disk('public')->exists($oggPublicPath),
        ]);

        return $oggPublicPath;
    }

    /**
     * Download file from R2 to temporary local storage.
     */
    private function downloadFromR2ToTemp(Upload $upload, string $r2FilePath): ?string
    {
        try {
            $tempFilePath = sys_get_temp_dir().'/'.Str::uuid().'_'.basename($r2FilePath);

            Log::info('AudioConversionService - Downloading from R2 to temp', [
                'upload_id' => $upload->id,
                'r2_path' => $r2FilePath,
                'temp_path' => $tempFilePath,
                'r2_file_exists' => Storage::disk('r2_private')->exists($r2FilePath),
            ]);

            if (! Storage::disk('r2_private')->exists($r2FilePath)) {
                Log::error('R2 private file does not exist', [
                    'upload_id' => $upload->id,
                    'r2_path' => $r2FilePath,
                ]);

                return null;
            }

            $r2Content = Storage::disk('r2_private')->get($r2FilePath);

            if ($r2Content && file_put_contents($tempFilePath, $r2Content)) {
                Log::info('AudioConversionService - File downloaded from R2 to temp', [
                    'upload_id' => $upload->id,
                    'temp_path' => $tempFilePath,
                    'file_size' => filesize($tempFilePath),
                ]);

                return $tempFilePath;
            }

            return null;
        } catch (\Exception $e) {
            Log::error('AudioConversionService - Failed to download from R2', [
                'upload_id' => $upload->id,
                'r2_path' => $r2FilePath,
                'error' => $e->getMessage(),
            ]);

            return null;
        }
    }

    /**
     * Convert audio file to OGG in temp directory.
     */
    private function convertToOggInTemp(string $sourceFilePath, string $publicFilePath): string
    {
        $tempDir = sys_get_temp_dir();
        $outputFileName = $this->generateOggFilename($publicFilePath);
        $outputPath = $tempDir.'/'.$outputFileName;

        // Setup FFMpeg with temp directory
        $ffmpeg = $this->createTempDiskFFMpeg($sourceFilePath);

        // Setup OGG format
        $format = new Vorbis;
        $format->setAudioChannels(2)->setAudioKiloBitrate(128);

        // Create output filesystem adapter
        $outputAdapter = new LocalFilesystemAdapter($tempDir);
        $outputFlysystemFilesystem = new Filesystem($outputAdapter);
        $outputDisk = new FilesystemAdapter(
            $outputFlysystemFilesystem,
            $outputAdapter,
            ['root' => $tempDir]
        );

        // Export to OGG
        $ffmpeg->export()->toDisk($outputDisk)->inFormat($format)->save($outputFileName);

        Log::info('AudioConversionService - Converted to OGG in temp', [
            'source_path' => $sourceFilePath,
            'output_path' => $outputPath,
            'output_exists' => file_exists($outputPath),
        ]);

        return $outputPath;
    }

    /**
     * Convert local file directly to public directory.
     */
    private function convertLocalFileToPublic(string $sourceFilePath, string $publicFilePath): string
    {
        // Setup FFMpeg for private disk
        if (! Storage::disk('private')->exists($sourceFilePath)) {
            throw new \Exception("Source file does not exist: {$sourceFilePath}");
        }

        $ffmpeg = FFMpeg::fromDisk('private')->open($sourceFilePath);

        // Setup OGG format
        $format = new Vorbis;
        $format->setAudioChannels(2)->setAudioKiloBitrate(128);

        // Generate OGG filename
        $oggFilePath = $this->replaceFileExtensionWithOgg($publicFilePath);

        // Export directly to public disk
        $ffmpeg->export()->toDisk('public')->inFormat($format)->save($oggFilePath);

        Log::info('AudioConversionService - Converted local file to public', [
            'source_path' => $sourceFilePath,
            'public_path' => $oggFilePath,
            'file_exists' => Storage::disk('public')->exists($oggFilePath),
        ]);

        return $oggFilePath;
    }

    /**
     * Create temporary disk FFMpeg instance.
     */
    private function createTempDiskFFMpeg(string $tempFilePath)
    {
        $tempDirPath = dirname($tempFilePath);
        $tempFileName = basename($tempFilePath);

        $adapter = new LocalFilesystemAdapter($tempDirPath);
        $flysystemFilesystem = new Filesystem($adapter);
        $tempDisk = new FilesystemAdapter(
            $flysystemFilesystem,
            $adapter,
            ['root' => $tempDirPath]
        );

        return FFMpeg::fromFilesystem($tempDisk)->open($tempFileName);
    }

    /**
     * Generate OGG filename from public path.
     */
    private function generateOggFilename(string $publicFilePath): string
    {
        $pathInfo = pathinfo($publicFilePath);

        return $pathInfo['filename'].'.ogg';
    }

    /**
     * Replace file extension with .ogg.
     */
    private function replaceFileExtensionWithOgg(string $filePath): string
    {
        $pathInfo = pathinfo($filePath);
        $directory = $pathInfo['dirname'] !== '.' ? $pathInfo['dirname'].'/' : '';

        return $directory.$pathInfo['filename'].'.ogg';
    }
}
