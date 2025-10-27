<?php

namespace Tests\Feature;

use App\Models\User;
use App\Services\AudioProcessingService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Log;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

final class AudioProcessingAbTestTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Clear any previous log entries
        Log::spy();
    }

    #[Test]
    public function audio_processing_service_always_uses_client_side_processing()
    {
        // Phase 4: Client-side processing is always enabled
        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService;

        $this->assertTrue($service->shouldUseClientSideProcessing());
    }

    #[Test]
    public function service_returns_consistent_results()
    {
        // Phase 4: Always returns true consistently
        $user = User::factory()->create(['id' => 1]);
        $this->actingAs($user);

        $service = new AudioProcessingService;

        // Multiple calls should all return true
        $result1 = $service->shouldUseClientSideProcessing();
        $result2 = $service->shouldUseClientSideProcessing();

        $this->assertTrue($result1);
        $this->assertTrue($result2);
        $this->assertEquals($result1, $result2);
    }

    #[Test]
    public function performance_metrics_are_always_logged()
    {
        // Phase 4: Metrics are always logged
        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService;

        $metrics = [
            'processing_type' => 'client',
            'processing_time_ms' => 1500,
            'file_size' => 5000000,
            'compression_ratio' => 0.3,
        ];

        $service->logPerformanceMetrics($metrics);

        Log::shouldHaveReceived('info')
            ->with('Audio processing performance metrics', \Mockery::on(function ($data) use ($user) {
                return $data['user_id'] === $user->id &&
                       $data['processing_type'] === 'client' &&
                       $data['processing_time_ms'] === 1500 &&
                       $data['file_size'] === 5000000 &&
                       $data['compression_ratio'] === 0.3 &&
                       isset($data['timestamp']);
            }));
    }

    #[Test]
    public function processing_errors_are_logged_with_user_context()
    {
        // Phase 4: Errors are logged but no fallback (client-side required)
        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService;
        $shouldFallback = $service->logProcessingError('Processing failed', 'client');

        $this->assertFalse($shouldFallback); // Phase 4: No fallback to server

        Log::shouldHaveReceived('error')
            ->with('Audio processing error', \Mockery::on(function ($data) use ($user) {
                return $data['user_id'] === $user->id &&
                       $data['processing_type'] === 'client' &&
                       $data['error'] === 'Processing failed' &&
                       isset($data['timestamp']);
            }));
    }

    #[Test]
    public function processing_success_logs_metrics_and_success()
    {
        // Phase 4: Always logs success and performance metrics
        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService;

        $data = [
            'processing_type' => 'client',
            'total_time_ms' => 2000,
            'upload_id' => 123,
            'final_status' => 'ready',
        ];

        $service->logProcessingSuccess($data);

        // Should log both success and performance metrics
        Log::shouldHaveReceived('info')
            ->with('Audio processing success', \Mockery::on(function ($logData) use ($user) {
                return $logData['user_id'] === $user->id &&
                       $logData['processing_type'] === 'client' &&
                       $logData['total_time_ms'] === 2000 &&
                       $logData['upload_id'] === 123 &&
                       $logData['final_status'] === 'ready' &&
                $logData['phase'] === 4 &&
                       isset($logData['timestamp']);
            }));

        Log::shouldHaveReceived('info')
            ->with('Audio processing performance metrics', \Mockery::on(function ($logData) use ($user) {
                return $logData['user_id'] === $user->id &&
                       $logData['processing_type'] === 'client' &&
                       isset($logData['timestamp']);
            }));
    }

    #[Test]
    public function frontend_config_includes_flags()
    {
        // Phase 4: Simplified config
        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService;
        $config = $service->getFrontendConfig();

        $this->assertArrayHasKey('client_side_processing_enabled', $config);
        $this->assertArrayHasKey('should_use_client_processing', $config);
        $this->assertArrayHasKey('monitor_performance', $config);

        $this->assertTrue($config['client_side_processing_enabled']);
        $this->assertTrue($config['should_use_client_processing']);
        $this->assertTrue($config['monitor_performance']);
    }
}
