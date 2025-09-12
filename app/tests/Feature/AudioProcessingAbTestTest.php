<?php

namespace Tests\Feature;

use App\Models\User;
use App\Services\AudioProcessingService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Log;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

/**
 * Tests for Audio Processing A/B Testing and Phase 3 features
 */
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
    public function audio_processing_service_respects_global_feature_flag()
    {
        Config::set('app.client_side_audio_processing', true);
        Config::set('app.audio_processing_ab_test.enabled', false);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        
        $this->assertTrue($service->shouldUseClientSideProcessing());
    }

    #[Test]
    public function audio_processing_service_falls_back_when_global_flag_disabled()
    {
        Config::set('app.client_side_audio_processing', false);
        Config::set('app.audio_processing_ab_test.enabled', false);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        
        $this->assertFalse($service->shouldUseClientSideProcessing());
    }

    #[Test]
    public function ab_test_assigns_users_consistently_based_on_user_id()
    {
        Config::set('app.client_side_audio_processing', false);
        Config::set('app.audio_processing_ab_test', [
            'enabled' => true,
            'client_percentage' => 50,
            'monitor_performance' => true,
            'fallback_on_error' => true,
        ]);

        $user = User::factory()->create(['id' => 1]);
        $this->actingAs($user);

        $service = new AudioProcessingService();
        
        // First call
        $result1 = $service->shouldUseClientSideProcessing();
        
        // Second call should be the same
        $result2 = $service->shouldUseClientSideProcessing();
        
        $this->assertEquals($result1, $result2);
    }

    #[Test]
    public function ab_test_logs_assignment_when_monitoring_enabled()
    {
        Config::set('app.client_side_audio_processing', false);
        Config::set('app.audio_processing_ab_test', [
            'enabled' => true,
            'client_percentage' => 50,
            'monitor_performance' => true,
            'fallback_on_error' => true,
        ]);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        $service->shouldUseClientSideProcessing();

        Log::shouldHaveReceived('info')
            ->with('Audio processing A/B test assignment', \Mockery::on(function ($data) use ($user) {
                return $data['user_id'] === $user->id &&
                       isset($data['assigned_to_client']) &&
                       isset($data['user_percentile']) &&
                       isset($data['client_percentage_threshold']);
            }));
    }

    #[Test]
    public function ab_test_does_not_log_when_monitoring_disabled()
    {
        Config::set('app.client_side_audio_processing', false);
        Config::set('app.audio_processing_ab_test', [
            'enabled' => true,
            'client_percentage' => 50,
            'monitor_performance' => false,
            'fallback_on_error' => true,
        ]);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        $service->shouldUseClientSideProcessing();

        Log::shouldNotHaveReceived('info');
    }

    #[Test]
    public function ab_test_percentage_zero_assigns_all_users_to_server()
    {
        Config::set('app.client_side_audio_processing', false);
        Config::set('app.audio_processing_ab_test', [
            'enabled' => true,
            'client_percentage' => 0,
            'monitor_performance' => false,
            'fallback_on_error' => true,
        ]);

        // Test multiple users to ensure consistency
        for ($i = 1; $i <= 10; $i++) {
            $user = User::factory()->create(['id' => $i]);
            $this->actingAs($user);

            $service = new AudioProcessingService();
            $this->assertFalse($service->shouldUseClientSideProcessing());
        }
    }

    #[Test]
    public function ab_test_percentage_hundred_assigns_all_users_to_client()
    {
        Config::set('app.client_side_audio_processing', false);
        Config::set('app.audio_processing_ab_test', [
            'enabled' => true,
            'client_percentage' => 100,
            'monitor_performance' => false,
            'fallback_on_error' => true,
        ]);

        // Test multiple users to ensure consistency
        for ($i = 1; $i <= 10; $i++) {
            $user = User::factory()->create(['id' => $i]);
            $this->actingAs($user);

            $service = new AudioProcessingService();
            $this->assertTrue($service->shouldUseClientSideProcessing());
        }
    }

    #[Test]
    public function performance_metrics_are_logged_when_monitoring_enabled()
    {
        Config::set('app.audio_processing_ab_test.monitor_performance', true);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        
        $metrics = [
            'processing_type' => 'client',
            'processing_time_ms' => 1500,
            'file_size' => 5000000,
            'compression_ratio' => 0.3,
        ];

        $service->logPerformanceMetrics($metrics);

        Log::shouldHaveReceived('info')
            ->with('Audio processing performance metrics', \Mockery::on(function ($data) use ($metrics, $user) {
                return $data['user_id'] === $user->id &&
                       $data['processing_type'] === 'client' &&
                       $data['processing_time_ms'] === 1500 &&
                       $data['file_size'] === 5000000 &&
                       $data['compression_ratio'] === 0.3 &&
                       isset($data['timestamp']);
            }));
    }

    #[Test]
    public function performance_metrics_are_not_logged_when_monitoring_disabled()
    {
        Config::set('app.audio_processing_ab_test.monitor_performance', false);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        
        $metrics = [
            'processing_type' => 'client',
            'processing_time_ms' => 1500,
        ];

        $service->logPerformanceMetrics($metrics);

        Log::shouldNotHaveReceived('info');
    }

    #[Test]
    public function processing_errors_are_logged_with_user_context()
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        $shouldFallback = $service->logProcessingError('Processing failed', 'client');

        $this->assertTrue($shouldFallback); // Should fallback by default

        Log::shouldHaveReceived('error')
            ->with('Audio processing error', \Mockery::on(function ($data) use ($user) {
                return $data['user_id'] === $user->id &&
                       $data['processing_type'] === 'client' &&
                       $data['error'] === 'Processing failed' &&
                       isset($data['timestamp']);
            }));
    }

    #[Test]
    public function processing_errors_respect_fallback_configuration()
    {
        Config::set('app.audio_processing_ab_test.fallback_on_error', false);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        $shouldFallback = $service->logProcessingError('Processing failed', 'client');

        $this->assertFalse($shouldFallback); // Should not fallback when disabled
    }

    #[Test]
    public function server_processing_errors_do_not_trigger_fallback()
    {
        Config::set('app.audio_processing_ab_test.fallback_on_error', true);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        $shouldFallback = $service->logProcessingError('Server processing failed', 'server');

        $this->assertFalse($shouldFallback); // Server errors don't trigger fallback
    }

    #[Test]
    public function processing_success_logs_metrics_and_success()
    {
        Config::set('app.audio_processing_ab_test.monitor_performance', true);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        
        $data = [
            'processing_type' => 'client',
            'total_time_ms' => 2000,
            'upload_id' => 123,
            'final_status' => 'ready',
        ];

        $service->logProcessingSuccess($data);

        // Should log both success and performance metrics
        Log::shouldHaveReceived('info')
            ->with('Audio processing success', \Mockery::on(function ($logData) use ($data, $user) {
                return $logData['user_id'] === $user->id &&
                       $logData['processing_type'] === 'client' &&
                       $logData['total_time_ms'] === 2000 &&
                       $logData['upload_id'] === 123 &&
                       $logData['final_status'] === 'ready' &&
                       isset($logData['timestamp']);
            }));

        Log::shouldHaveReceived('info')
            ->with('Audio processing performance metrics', \Mockery::on(function ($logData) use ($data, $user) {
                return $logData['user_id'] === $user->id &&
                       $logData['processing_type'] === 'client' &&
                       isset($logData['timestamp']);
            }));
    }

    #[Test]
    public function frontend_config_includes_all_necessary_flags()
    {
        Config::set('app.client_side_audio_processing', true);
        Config::set('app.audio_processing_ab_test', [
            'enabled' => true,
            'client_percentage' => 75,
            'monitor_performance' => true,
            'fallback_on_error' => true,
        ]);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        $config = $service->getFrontendConfig();

        $this->assertArrayHasKey('client_side_processing_enabled', $config);
        $this->assertArrayHasKey('ab_test_enabled', $config);
        $this->assertArrayHasKey('should_use_client_processing', $config);
        $this->assertArrayHasKey('fallback_on_error', $config);
        $this->assertArrayHasKey('monitor_performance', $config);

        $this->assertTrue($config['client_side_processing_enabled']);
        $this->assertTrue($config['ab_test_enabled']);
        $this->assertTrue($config['fallback_on_error']);
        $this->assertTrue($config['monitor_performance']);
        $this->assertIsBool($config['should_use_client_processing']);
    }

    #[Test]
    public function frontend_config_handles_disabled_features()
    {
        Config::set('app.client_side_audio_processing', false);
        Config::set('app.audio_processing_ab_test', [
            'enabled' => false,
            'client_percentage' => 0,
            'monitor_performance' => false,
            'fallback_on_error' => false,
        ]);

        $user = User::factory()->create();
        $this->actingAs($user);

        $service = new AudioProcessingService();
        $config = $service->getFrontendConfig();

        $this->assertFalse($config['client_side_processing_enabled']);
        $this->assertFalse($config['ab_test_enabled']);
        $this->assertFalse($config['should_use_client_processing']);
        $this->assertFalse($config['fallback_on_error']);
        $this->assertFalse($config['monitor_performance']);
    }
}