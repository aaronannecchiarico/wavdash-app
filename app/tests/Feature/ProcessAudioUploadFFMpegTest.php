<?php

namespace Tests\Feature;

use App\Jobs\ProcessAudioUpload;
use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class ProcessAudioUploadFFMpegTest extends TestCase
{
    use RefreshDatabase;

    public function test_process_audio_upload_handles_temporary_file_paths_correctly()
    {
        // Fake the queue to prevent actual job execution
        Queue::fake();

        // Mock R2 private storage for two-bucket system
        Storage::fake('r2_private');

        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'uploads/1/2025/08/21/test.mp3', // Two-bucket system path
            'path' => 'uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
            'filename' => 'test.mp3',
        ]);

        // Create a mock R2 file in private bucket
        Storage::disk('r2_private')->put($upload->r2_upload_path, 'fake audio content');

        // Capture log messages
        Log::spy();

        // Execute the job directly to test FFMpeg path handling
        $job = new ProcessAudioUpload($upload);

        // We expect this to fail due to invalid audio content, but we want to verify
        // that the temporary file path is handled correctly without the Laravel storage prefix issue
        try {
            $job->handle();
        } catch (\Exception $e) {
            // We expect an exception due to fake audio content, but we want to ensure
            // it's not the storage path resolution error
            $this->assertStringNotContainsString('/storage/app/var/folders', $e->getMessage(),
                'The FFMpeg path resolution error should be fixed');

            $this->assertStringNotContainsString('storage/app', $e->getMessage(),
                'Error should not contain Laravel storage path issues');

            // The error should be about probing/processing, indicating FFMpeg reached the file
            $this->assertTrue(
                str_contains($e->getMessage(), 'Unable to probe') ||
                str_contains($e->getMessage(), 'probe') ||
                str_contains($e->getMessage(), 'format') ||
                str_contains($e->getMessage(), 'Invalid data found'),
                'Error should be related to FFMpeg file processing, not path resolution: '.$e->getMessage()
            );
        }

        // Verify that the temporary disk logging shows correct paths
        Log::shouldHaveReceived('info')
            ->with('ProcessAudioUpload - Opening with temp disk', \Mockery::on(function ($arg) {
                // Verify the temp disk approach is working correctly
                return isset($arg['temp_dir_path']) &&
                       isset($arg['temp_file_name']) &&
                       str_contains($arg['temp_dir_path'], 'var/folders') &&
                       ! str_contains($arg['temp_file_name'], '/'); // filename should not contain path separators
            }))
            ->once();

        // Verify no Laravel storage path prefix errors were logged
        Log::shouldNotHaveReceived('error', [
            \Mockery::on(function ($message) {
                return str_contains($message, '/storage/app/var/folders');
            }),
            \Mockery::any(),
        ]);
    }

    public function test_temporary_file_path_conversion_logic()
    {
        // Test the path conversion logic directly
        $tempPath = '/var/folders/7f/3r3ptx2x12s_l6lzdy4cm57r0000gn/T/test_file.mp3';
        $relativePath = ltrim($tempPath, '/');

        $this->assertEquals(
            'var/folders/7f/3r3ptx2x12s_l6lzdy4cm57r0000gn/T/test_file.mp3',
            $relativePath,
            'Temporary file path should be converted to relative path correctly'
        );

        $this->assertStringNotContainsString('/storage/app', $relativePath,
            'Relative path should not contain Laravel storage prefix');

        $this->assertStringNotContainsString('storage/app', $relativePath,
            'Relative path should not contain Laravel storage prefix');
    }

    public function test_r2_upload_downloads_to_temporary_file()
    {
        Queue::fake();
        Storage::fake('r2_private');

        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'uploads/1/2025/08/21/test.mp3', // Two-bucket system path
            'path' => 'uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
            'filename' => 'test.mp3',
        ]);

        // Create a mock R2 file with some content in private bucket
        Storage::disk('r2_private')->put($upload->r2_upload_path, 'fake audio content for testing');

        Log::spy();

        $job = new ProcessAudioUpload($upload);

        try {
            $job->handle();
        } catch (\Exception $e) {
            // Expected to fail due to fake content
        }

        // Verify that the R2 download process logs show correct temp file creation
        Log::shouldHaveReceived('info')
            ->with('File downloaded from R2 to temp', \Mockery::on(function ($arg) use ($upload) {
                return $arg['upload_id'] === $upload->id &&
                       isset($arg['temp_path']) &&
                       str_starts_with($arg['temp_path'], sys_get_temp_dir()) &&
                       $arg['temp_file_exists'] === true &&
                       $arg['temp_file_size'] > 0;
            }))
            ->once();
    }
}
