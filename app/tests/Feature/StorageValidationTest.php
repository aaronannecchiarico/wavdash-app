<?php

namespace Tests\Feature;

use App\Jobs\ProcessAudioUpload;
use App\Models\Upload;
use App\Models\User;
use App\Services\AudioAnalysisService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Queue;
use Tests\TestCase;

class StorageValidationTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Enable audio analysis for these tests
        Config::set('services.audio_analysis.enabled', true);
        Config::set('services.audio_analysis.base_url', 'http://localhost:8001');
    }

    public function test_storage_validation_passes_when_types_match_r2()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'private/uploads/1/2025/08/21/test.mp3',
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Mock microservice response for R2 storage
        Http::fake([
            'localhost:8001/storage/status' => Http::response([
                'enabled' => true,
                'storage_type' => 'r2',
                'message' => 'R2 storage is enabled and ready',
            ], 200),
        ]);

        $audioAnalysisService = app(AudioAnalysisService::class);
        $result = $audioAnalysisService->validateStorageCompatibility($upload);

        $this->assertTrue($result['compatible']);
        $this->assertEquals('r2', $result['laravel_storage_type']);
        $this->assertEquals('r2', $result['microservice_storage_type']);
        $this->assertTrue($result['microservice_enabled']);
        $this->assertStringContainsString('Storage types match (r2)', $result['message']);
    }

    public function test_storage_validation_passes_when_types_match_local()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => false,
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Mock microservice response for local storage
        Http::fake([
            'localhost:8001/storage/status' => Http::response([
                'enabled' => true,
                'storage_type' => 'local',
                'message' => 'Local storage is enabled and ready',
            ], 200),
        ]);

        $audioAnalysisService = app(AudioAnalysisService::class);
        $result = $audioAnalysisService->validateStorageCompatibility($upload);

        $this->assertTrue($result['compatible']);
        $this->assertEquals('local', $result['laravel_storage_type']);
        $this->assertEquals('local', $result['microservice_storage_type']);
        $this->assertTrue($result['microservice_enabled']);
        $this->assertStringContainsString('Storage types match (local)', $result['message']);
    }

    public function test_storage_validation_fails_when_types_mismatch()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'private/uploads/1/2025/08/21/test.mp3',
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Mock microservice response with different storage type
        Http::fake([
            'localhost:8001/storage/status' => Http::response([
                'enabled' => true,
                'storage_type' => 'local',
                'message' => 'Local storage is enabled and ready',
            ], 200),
        ]);

        $audioAnalysisService = app(AudioAnalysisService::class);
        $result = $audioAnalysisService->validateStorageCompatibility($upload);

        $this->assertFalse($result['compatible']);
        $this->assertEquals('r2', $result['laravel_storage_type']);
        $this->assertEquals('local', $result['microservice_storage_type']);
        $this->assertTrue($result['microservice_enabled']);
        $this->assertStringContainsString('Storage type mismatch: Laravel uses r2, microservice uses local', $result['message']);
    }

    public function test_storage_validation_fails_when_microservice_disabled()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'private/uploads/1/2025/08/21/test.mp3',
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Mock microservice response with storage disabled
        Http::fake([
            'localhost:8001/storage/status' => Http::response([
                'enabled' => false,
                'storage_type' => 'r2',
                'message' => 'R2 storage is disabled',
            ], 200),
        ]);

        $audioAnalysisService = app(AudioAnalysisService::class);
        $result = $audioAnalysisService->validateStorageCompatibility($upload);

        $this->assertFalse($result['compatible']);
        $this->assertEquals('r2', $result['laravel_storage_type']);
        $this->assertEquals('r2', $result['microservice_storage_type']);
        $this->assertFalse($result['microservice_enabled']);
        $this->assertStringContainsString('Storage type mismatch: Laravel uses r2, microservice uses r2', $result['message']);
    }

    public function test_storage_validation_handles_microservice_unavailable()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'private/uploads/1/2025/08/21/test.mp3',
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Mock microservice failure
        Http::fake([
            'localhost:8001/storage/status' => Http::response('Service unavailable', 503),
        ]);

        $audioAnalysisService = app(AudioAnalysisService::class);
        $result = $audioAnalysisService->validateStorageCompatibility($upload);

        $this->assertFalse($result['compatible']);
        $this->assertEquals('r2', $result['laravel_storage_type']);
        $this->assertEquals('unknown', $result['microservice_storage_type']);
        $this->assertFalse($result['microservice_enabled']);
        $this->assertStringContainsString('Failed to validate storage compatibility', $result['message']);
        $this->assertArrayHasKey('error', $result);
    }

    public function test_process_audio_upload_validates_storage_when_analysis_enabled()
    {
        // Fake the queue to prevent actual job execution
        Queue::fake();

        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'private/uploads/1/2025/08/21/test.mp3',
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Mock microservice response
        Http::fake([
            'localhost:8001/storage/status' => Http::response([
                'enabled' => true,
                'storage_type' => 'r2',
                'message' => 'R2 storage is enabled and ready',
            ], 200),
        ]);

        // Capture log messages
        Log::spy();

        // Execute the job directly to test validation
        $job = new ProcessAudioUpload($upload);

        // We expect this to fail due to missing file, but we want to verify validation runs
        try {
            $job->handle();
        } catch (\Exception $e) {
            // Expected to fail due to missing actual file, that's okay
        }

        // Verify storage validation was logged
        Log::shouldHaveReceived('info')
            ->with('ProcessAudioUpload - Storage compatibility validated successfully', \Mockery::on(function ($arg) use ($upload) {
                return $arg['upload_id'] === $upload->id &&
                       isset($arg['validation_message']) &&
                       str_contains($arg['validation_message'], 'Storage types match (r2)');
            }))
            ->once();
    }

    public function test_process_audio_upload_logs_storage_mismatch_but_continues()
    {
        // Fake the queue to prevent actual job execution
        Queue::fake();

        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'private/uploads/1/2025/08/21/test.mp3',
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Mock microservice response with mismatch
        Http::fake([
            'localhost:8001/storage/status' => Http::response([
                'enabled' => true,
                'storage_type' => 'local',
                'message' => 'Local storage is enabled and ready',
            ], 200),
        ]);

        // Capture log messages
        Log::spy();

        // Execute the job directly to test validation
        $job = new ProcessAudioUpload($upload);

        // We expect this to fail due to missing file, but we want to verify validation runs
        try {
            $job->handle();
        } catch (\Exception $e) {
            // Expected to fail due to missing actual file, that's okay
        }

        // Verify storage validation failure was logged
        Log::shouldHaveReceived('warning')
            ->with('ProcessAudioUpload - Storage compatibility validation failed', \Mockery::on(function ($arg) use ($upload) {
                return $arg['upload_id'] === $upload->id &&
                       isset($arg['validation_result']) &&
                       $arg['validation_result']['compatible'] === false;
            }))
            ->once();
    }

    public function test_process_audio_upload_skips_validation_when_analysis_disabled()
    {
        // Disable audio analysis
        Config::set('services.audio_analysis.enabled', false);

        // Fake the queue to prevent actual job execution
        Queue::fake();

        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'uses_r2_storage' => true,
            'r2_upload_path' => 'private/uploads/1/2025/08/21/test.mp3',
            'path' => 'private/uploads/1/2025/08/21/test.mp3',
            'status' => 'pending',
        ]);

        // Don't mock any HTTP calls - validation should be skipped

        // Capture log messages
        Log::spy();

        // Execute the job directly
        $job = new ProcessAudioUpload($upload);

        // We expect this to fail due to missing file, but we want to verify validation is skipped
        try {
            $job->handle();
        } catch (\Exception $e) {
            // Expected to fail due to missing actual file, that's okay
        }

        // Verify no storage validation logs occurred
        Log::shouldNotHaveReceived('info', [
            'ProcessAudioUpload - Storage compatibility validated successfully',
            \Mockery::any(),
        ]);

        Log::shouldNotHaveReceived('warning', [
            'ProcessAudioUpload - Storage compatibility validation failed',
            \Mockery::any(),
        ]);
    }
}
