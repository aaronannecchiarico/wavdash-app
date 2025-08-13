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
        $filename = $this->faker->uuid . '.mp3';
        return [
            'user_id' => \App\Models\User::factory(),
            'title' => $this->faker->words(3, true),
            'description' => $this->faker->optional()->paragraph(),
            'genre' => $this->faker->randomElement(['Hip Hop', 'Electronic', 'Pop', 'Rock', 'Jazz', 'Classical', 'Lo-Fi']),
            'filename' => $filename,
            'path' => 'uploads/original/' . $filename,
            'stream_path' => null,
            'mime_type' => 'audio/mpeg',
            'size' => $this->faker->numberBetween(1000000, 10000000),
            'status' => 'pending',
            'duration_seconds' => null,
            'uses_r2_storage' => false,
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
                $storageDisk = $disk === 'local' ? 'private' : $disk;
                
                $filename = Str::uuid() . '.wav';
                $streamFilename = Str::slug(pathinfo('test_audio', PATHINFO_FILENAME)) . '-' . Str::uuid() . '.ogg';
                $date = now();
                
                // Create user-organized path structure for original file
                $targetPath = sprintf(
                    'uploads/%s/%s/%s',
                    $upload->user_id,
                    $date->format('Y/m/d'),
                    $filename
                );
                
                // Create user-organized path structure for stream file
                $streamPath = sprintf(
                    'uploads/stream/%s/%s/%s',
                    $upload->user_id,
                    $date->format('Y/m/d'),
                    $streamFilename
                );
                
                // Copy original file to private storage
                $content = file_get_contents($sourcePath);
                Storage::disk($storageDisk)->put($targetPath, $content);
                
                // Copy file to public storage as stream file (for seeding purposes)
                // In real usage, this would be converted by ProcessAudioUpload job
                Storage::disk('public')->put($streamPath, $content);
                
                // Update the upload record with real file data
                $upload->update([
                    'filename' => 'test_audio.wav',
                    'path' => $targetPath,
                    'stream_path' => $streamPath,
                    'mime_type' => 'audio/wav',
                    'size' => filesize($sourcePath),
                    'status' => 'ready', // Mark as ready since we're providing the stream file
                    'duration_seconds' => 2, // Test audio is ~2 seconds
                ]);
            }
        });
    }
}
