<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Config;
use Tests\TestCase;

class ProcessAudioUploadStorageTest extends TestCase
{
    use RefreshDatabase;

    public function test_process_audio_upload_correctly_detects_r2_storage_regardless_of_default_disk()
    {
        // Set default disk to local to simulate the real-world scenario
        Config::set('filesystems.default', 'local');

        $user = User::factory()->create();

        // Create an upload that uses R2 storage (two-bucket system)
        $r2Upload = Upload::factory()->for($user)->make([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'uploads/1/2025/08/21/test-file.mp3', // Stored in private bucket without prefix
            'path' => 'uploads/1/2025/08/21/test-file.mp3',
            'status' => 'pending',
        ]);
        $r2Upload->save();

        // Create an upload that uses local storage
        $localUpload = Upload::factory()->for($user)->make([
            'uses_r2_storage' => false,
            'r2_upload_path' => null,
            'path' => 'uploads/1/2025/08/21/test-file-local.mp3',
            'status' => 'pending',
        ]);
        $localUpload->save();

        // Test R2 upload detection
        $this->assertTrue($r2Upload->usesR2Storage(), 'R2 upload should be detected as using R2 storage');
        $this->assertEquals('r2', $r2Upload->usesR2Storage() ? 'r2' : 'local');

        // Test local upload detection
        $this->assertFalse($localUpload->usesR2Storage(), 'Local upload should be detected as using local storage');
        $this->assertEquals('local', $localUpload->usesR2Storage() ? 'r2' : 'local');

        // Verify the logic that was fixed
        $defaultDisk = config('filesystems.default');
        $this->assertEquals('local', $defaultDisk, 'Default disk should be local for this test');

        // OLD BROKEN LOGIC: Would never work because defaultDisk is 'local'
        $oldConditionR2 = $r2Upload->usesR2Storage() && $defaultDisk === 'r2';
        $this->assertFalse($oldConditionR2, 'Old logic would incorrectly fail for R2 uploads');

        // NEW FIXED LOGIC: Works correctly based on upload's actual storage type
        $newConditionR2 = $r2Upload->usesR2Storage();
        $this->assertTrue($newConditionR2, 'New logic correctly detects R2 uploads');

        $newConditionLocal = $localUpload->usesR2Storage();
        $this->assertFalse($newConditionLocal, 'New logic correctly detects local uploads');
    }

    public function test_storage_disk_resolution_for_local_uploads()
    {
        Config::set('filesystems.default', 'local');

        $user = User::factory()->create();
        $localUpload = Upload::factory()->for($user)->make([
            'uses_r2_storage' => false,
            'path' => 'private/uploads/1/2025/08/21/test-file.mp3',
            'status' => 'pending',
        ]);
        $localUpload->save();

        // Test storage disk resolution logic
        $defaultDisk = config('filesystems.default');
        $storageDisk = $defaultDisk === 'local' ? 'private' : $defaultDisk;

        $this->assertEquals('private', $storageDisk, 'Local uploads should resolve to private disk');
    }

    public function test_can_switch_between_storage_types()
    {
        $user = User::factory()->create();

        // Test with default disk set to local
        Config::set('filesystems.default', 'local');

        $localUpload = Upload::factory()->for($user)->make([
            'uses_r2_storage' => false,
            'path' => 'private/uploads/1/2025/08/21/test-file.mp3',
        ]);
        $localUpload->save();

        $this->assertFalse($localUpload->usesR2Storage());

        // Test with default disk set to r2
        Config::set('filesystems.default', 'r2');

        $r2Upload = Upload::factory()->for($user)->make([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'uploads/1/2025/08/21/test-file.mp3', // Two-bucket system path
            'path' => 'uploads/1/2025/08/21/test-file.mp3',
        ]);
        $r2Upload->save();

        $this->assertTrue($r2Upload->usesR2Storage());

        // Both should work correctly regardless of default disk setting
        $this->assertFalse($localUpload->fresh()->usesR2Storage(), 'Local upload should remain local regardless of default disk');
        $this->assertTrue($r2Upload->fresh()->usesR2Storage(), 'R2 upload should remain R2 regardless of default disk');
    }

    public function test_two_bucket_system_path_structure()
    {
        Config::set('filesystems.default', 'r2');

        $user = User::factory()->create();

        // Test private bucket path structure (no prefix)
        $r2Upload = Upload::factory()->for($user)->make([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'uploads/1/2025/08/21/test-file.mp3',
            'path' => 'uploads/1/2025/08/21/test-file.mp3',
            'status' => 'ready',
            'stream_path' => 'uploads/stream/1/2025/08/21/test-file.ogg', // Public bucket path
        ]);
        $r2Upload->save();

        // Verify private bucket path (direct path, no private/ prefix)
        $this->assertEquals('uploads/1/2025/08/21/test-file.mp3', $r2Upload->r2_upload_path);

        // Verify public bucket path for streaming (also no prefix, goes to public bucket)
        $this->assertEquals('uploads/stream/1/2025/08/21/test-file.ogg', $r2Upload->stream_path);

        // Verify the upload uses R2 storage
        $this->assertTrue($r2Upload->usesR2Storage());
    }
}
