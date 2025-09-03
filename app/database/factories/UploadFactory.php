<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Upload>
 */
class UploadFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        // Use mock data for basic factory - real file copying will be handled in configure()
        $filename = $this->faker->uuid.'.mp3';
        $defaultDisk = config('filesystems.default');
        $usesR2Storage = $defaultDisk === 'r2';

        return [
            // Don't set user_id here - let it be set by the for() relationship
            'title' => $this->faker->words(3, true),
            'description' => $this->faker->optional()->paragraph(),
            'genre' => $this->faker->randomElement(['Hip Hop', 'Electronic', 'Pop', 'Rock', 'Jazz', 'Classical', 'Lo-Fi']),
            'filename' => $filename,
            'path' => 'uploads/original/'.$filename,
            'stream_path' => null,
            'mime_type' => 'audio/mpeg',
            'size' => $this->faker->numberBetween(10000, 100000), // 10KB to 100KB
            'status' => 'pending',
            'duration_seconds' => null,
            'uses_r2_storage' => $usesR2Storage,
            'r2_upload_path' => null, // Will be set in configure() if R2
        ];
    }

    /**
     * Configure the model factory to use the test audio file.
     */
    public function configure()
    {
        return $this->afterCreating(function (\App\Models\Upload $upload) {
            $sourcePath = base_path('test_audio.wav');

            if (file_exists($sourcePath)) {
                $disk = config('filesystems.default');
                $filename = Str::uuid().'.wav';
                $streamFilename = Str::slug(pathinfo('test_audio', PATHINFO_FILENAME)).'-'.Str::uuid().'.ogg';
                $date = now();
                $content = file_get_contents($sourcePath);

                // Check if R2 storage is enabled based on default disk, not usesR2Storage() method
                if ($upload->uses_r2_storage) {
                    // R2 Storage paths using two-bucket system (no prefixes)
                    $targetPath = sprintf(
                        'uploads/%s/%s/%s',
                        $upload->user_id,
                        $date->format('Y/m/d'),
                        $filename
                    );

                    $streamPath = sprintf(
                        'uploads/stream/%s/%s/%s',
                        $upload->user_id,
                        $date->format('Y/m/d'),
                        $streamFilename
                    );

                    // Upload original file to R2 private bucket
                    Storage::disk('r2_private')->put($targetPath, $content);

                    // Upload stream file to R2 public bucket
                    Storage::disk('r2_public')->put($streamPath, $content);

                    // Update the upload record with R2 paths
                    $upload->update([
                        'filename' => 'test_audio.wav',
                        'path' => $targetPath,
                        'r2_upload_path' => $targetPath,
                        'stream_path' => $streamPath,
                        'mime_type' => 'audio/wav',
                        'size' => filesize($sourcePath),
                        'status' => 'ready',
                        'duration_seconds' => 2,
                    ]);
                } else {
                    // Local Storage paths
                    $storageDisk = $disk === 'local' ? 'private' : $disk;

                    $targetPath = sprintf(
                        'uploads/%s/%s/%s',
                        $upload->user_id,
                        $date->format('Y/m/d'),
                        $filename
                    );

                    $streamPath = sprintf(
                        'uploads/stream/%s/%s/%s',
                        $upload->user_id,
                        $date->format('Y/m/d'),
                        $streamFilename
                    );

                    // Copy original file to private storage
                    Storage::disk($storageDisk)->put($targetPath, $content);

                    // Copy file to public storage as stream file (for seeding purposes)
                    Storage::disk('public')->put($streamPath, $content);

                    // Update the upload record with local paths
                    $upload->update([
                        'filename' => 'test_audio.wav',
                        'path' => $targetPath,
                        'stream_path' => $streamPath,
                        'mime_type' => 'audio/wav',
                        'size' => filesize($sourcePath),
                        'status' => 'ready',
                        'duration_seconds' => 2,
                    ]);
                }
            }
        });
    }
}
