<?php

namespace Tests\Unit;

use App\Models\Upload;
use App\Models\User;
use App\Services\R2StorageService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class R2StorageServiceTest extends TestCase
{
    use RefreshDatabase;

    private R2StorageService $r2Service;

    protected function setUp(): void
    {
        parent::setUp();
        $this->r2Service = new R2StorageService;
    }

    public function test_is_enabled_returns_false_when_r2_disabled(): void
    {
        Config::set('filesystems.default', 'local');

        $this->assertFalse($this->r2Service->isEnabled());
    }

    public function test_is_enabled_returns_false_when_credentials_missing(): void
    {
        Config::set('filesystems.default', 'r2');
        Config::set('filesystems.disks.r2.key', '');
        Config::set('filesystems.disks.r2.secret', '');

        $this->assertFalse($this->r2Service->isEnabled());
    }

    public function test_is_enabled_returns_true_when_properly_configured(): void
    {
        Config::set('filesystems.default', 'r2');
        Config::set('filesystems.disks.r2.key', 'test-key');
        Config::set('filesystems.disks.r2.secret', 'test-secret');
        Config::set('filesystems.disks.r2.endpoint', 'https://test.r2.cloudflarestorage.com');

        $this->assertTrue($this->r2Service->isEnabled());
    }

    public function test_upload_file_returns_null_when_disabled(): void
    {
        Config::set('filesystems.default', 'local');

        $file = UploadedFile::fake()->create('test.mp3', 10, 'audio/mpeg');

        $result = $this->r2Service->uploadFile($file);

        $this->assertNull($result);
    }

    public function test_upload_file_returns_path_when_successful(): void
    {
        $this->enableR2();

        Storage::fake('r2');

        $file = UploadedFile::fake()->create('test.mp3', 10, 'audio/mpeg');

        $result = $this->r2Service->uploadFile($file, 'uploads');

        $this->assertNotNull($result);
        $this->assertStringStartsWith('uploads/', $result);
        $this->assertStringEndsWith('.mp3', $result);
    }

    public function test_get_file_returns_null_when_disabled(): void
    {
        Config::set('filesystems.default', 'local');

        $result = $this->r2Service->getFile('test/path.mp3');

        $this->assertNull($result);
    }

    public function test_get_file_returns_content_when_exists(): void
    {
        $this->enableR2();

        Storage::fake('r2');
        Storage::disk('r2')->put('test/path.mp3', 'test content');

        $result = $this->r2Service->getFile('test/path.mp3');

        $this->assertEquals('test content', $result);
    }

    public function test_file_exists_returns_false_when_disabled(): void
    {
        Config::set('filesystems.default', 'local');

        $result = $this->r2Service->fileExists('test/path.mp3');

        $this->assertFalse($result);
    }

    public function test_file_exists_checks_storage(): void
    {
        $this->enableR2();

        Storage::fake('r2');
        Storage::disk('r2')->put('test/exists.mp3', 'content');

        $this->assertTrue($this->r2Service->fileExists('test/exists.mp3'));
        $this->assertFalse($this->r2Service->fileExists('test/missing.mp3'));
    }

    public function test_delete_file_returns_false_when_disabled(): void
    {
        Config::set('filesystems.default', 'local');

        $result = $this->r2Service->deleteFile('test/path.mp3');

        $this->assertFalse($result);
    }

    public function test_delete_file_removes_existing_file(): void
    {
        $this->enableR2();

        Storage::fake('r2');
        Storage::disk('r2')->put('test/delete.mp3', 'content');

        $this->assertTrue($this->r2Service->fileExists('test/delete.mp3'));

        $result = $this->r2Service->deleteFile('test/delete.mp3');

        $this->assertTrue($result);
        $this->assertFalse($this->r2Service->fileExists('test/delete.mp3'));
    }

    public function test_get_public_url_returns_null_when_no_public_url_configured(): void
    {
        Config::set('filesystems.disks.r2.url', null);

        $result = $this->r2Service->getPublicUrl('test/path.mp3');

        $this->assertNull($result);
    }

    public function test_get_public_url_returns_formatted_url(): void
    {
        Config::set('filesystems.disks.r2.url', 'https://bucket.r2.dev');

        $result = $this->r2Service->getPublicUrl('test/path.mp3');

        $this->assertEquals('https://bucket.r2.dev/test/path.mp3', $result);
    }

    public function test_upload_stems_returns_empty_when_disabled(): void
    {
        Config::set('filesystems.default', 'local');

        $result = $this->r2Service->uploadStems(['vocals' => '/tmp/vocals.wav'], 'test-base');

        $this->assertEmpty($result);
    }

    public function test_upload_stems_uploads_multiple_files(): void
    {
        $this->enableR2();

        Storage::fake('r2');

        // Create temporary files
        $vocalsPath = tempnam(sys_get_temp_dir(), 'vocals').'.wav';
        $drumsPath = tempnam(sys_get_temp_dir(), 'drums').'.wav';
        file_put_contents($vocalsPath, 'vocals content');
        file_put_contents($drumsPath, 'drums content');

        $stems = [
            'vocals' => $vocalsPath,
            'drums' => $drumsPath,
        ];

        $result = $this->r2Service->uploadStems($stems, 'test-base');

        $this->assertCount(2, $result);
        $this->assertArrayHasKey('vocals', $result);
        $this->assertArrayHasKey('drums', $result);
        $this->assertEquals('stems/test-base/vocals.wav', $result['vocals']);
        $this->assertEquals('stems/test-base/drums.wav', $result['drums']);

        // Cleanup
        unlink($vocalsPath);
        unlink($drumsPath);
    }

    public function test_get_storage_info_returns_configuration(): void
    {
        // Set up R2 configuration to match current implementation
        Config::set('filesystems.default', 'r2');
        Config::set('filesystems.disks.r2.key', 'test-key');
        Config::set('filesystems.disks.r2.secret', 'test-secret');
        Config::set('filesystems.disks.r2.bucket', 'test-bucket');
        Config::set('filesystems.disks.r2.endpoint', 'https://test.endpoint');
        Config::set('filesystems.disks.r2.url', 'https://public.url');

        $result = $this->r2Service->getStorageInfo();

        $this->assertIsArray($result);
        $this->assertEquals(true, $result['enabled']);
        $this->assertEquals('r2', $result['disk']);
        $this->assertEquals('test-bucket', $result['bucket']);
        $this->assertEquals('https://test.endpoint', $result['endpoint']);
        $this->assertEquals('https://public.url', $result['public_url']);
    }

    public function test_migrate_upload_returns_false_when_disabled(): void
    {
        // Set filesystem to local to disable R2
        Config::set('filesystems.default', 'local');

        $user = User::factory()->create();
        $upload = Upload::factory()->create([
            'user_id' => $user->id,
            'uses_r2_storage' => false,
        ]);

        $result = $this->r2Service->migrateUpload($upload);

        $this->assertFalse($result);
    }

    public function test_migrate_upload_returns_false_when_already_using_r2(): void
    {
        $this->enableR2();

        $user = User::factory()->create();
        $upload = Upload::factory()->create([
            'user_id' => $user->id,
            'uses_r2_storage' => true,
        ]);

        $result = $this->r2Service->migrateUpload($upload);

        $this->assertFalse($result);
    }

    public function test_copy_from_local_returns_false_when_disabled(): void
    {
        Config::set('filesystems.default', 'local');

        $result = $this->r2Service->copyFromLocal('/tmp/nonexistent', 'r2/path');

        $this->assertFalse($result);
    }

    public function test_copy_from_local_returns_false_when_file_missing(): void
    {
        $this->enableR2();

        $result = $this->r2Service->copyFromLocal('/tmp/nonexistent-file', 'r2/path');

        $this->assertFalse($result);
    }

    public function test_copy_from_local_uploads_file_content(): void
    {
        $this->enableR2();

        Storage::fake('r2');

        // Create temporary file
        $tempFile = tempnam(sys_get_temp_dir(), 'test');
        file_put_contents($tempFile, 'test content');

        $result = $this->r2Service->copyFromLocal($tempFile, 'uploads/copied.txt');

        $this->assertTrue($result);
        $this->assertTrue(Storage::disk('r2')->exists('uploads/copied.txt'));
        $this->assertEquals('test content', Storage::disk('r2')->get('uploads/copied.txt'));

        // Cleanup
        unlink($tempFile);
    }

    private function enableR2(): void
    {
        Config::set('filesystems.default', 'r2');
        Config::set('filesystems.disks.r2.key', 'test-key');
        Config::set('filesystems.disks.r2.secret', 'test-secret');
        Config::set('filesystems.disks.r2.endpoint', 'https://test.r2.cloudflarestorage.com');
    }
}
