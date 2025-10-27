<?php

use App\Services\AudioMicroserviceMigrationService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class AudioMicroserviceMigrationTest extends TestCase
{
    use RefreshDatabase;

    #[\PHPUnit\Framework\Attributes\Test]
    public function service_correctly_checks_availability_when_microservice_is_not_running()
    {
        // Mock HTTP calls to simulate microservice not running
        Http::fake([
            '*/migration/status' => Http::response([], 500),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);

        $this->assertFalse($service->isAvailable());
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function service_correctly_identifies_available_microservice()
    {
        // Mock HTTP calls to simulate available microservice
        Http::fake([
            '*/migration/status' => Http::response([
                'debug_mode' => true,
                'migration_available' => true,
                'seeding_available' => true,
            ], 200),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);

        $this->assertTrue($service->isAvailable());
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function service_correctly_identifies_production_microservice()
    {
        // Mock HTTP calls to simulate production microservice (debug_mode: false)
        Http::fake([
            '*/migration/status' => Http::response([
                'debug_mode' => false,
                'migration_available' => false,
                'seeding_available' => false,
            ], 200),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);

        $this->assertFalse($service->isAvailable());
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function fresh_migration_returns_success_response()
    {
        Http::fake([
            '*/migration/fresh' => Http::response([
                'success' => true,
                'message' => 'Fresh migration and seeding completed successfully',
                'details' => [
                    'steps_completed' => ['migrate_fresh.py', 'seed_data.py'],
                    'steps_failed' => [],
                    'warnings' => [],
                ],
            ], 200),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);
        $result = $service->runFreshMigration();

        $this->assertTrue($result['success']);
        $this->assertEquals('Fresh migration and seeding completed successfully', $result['message']);
        $this->assertArrayHasKey('details', $result);
        $this->assertCount(2, $result['details']['steps_completed']);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function fresh_migration_handles_failure_response()
    {
        Http::fake([
            '*/migration/fresh' => Http::response([
                'success' => false,
                'message' => 'Migration failed due to Redis connection error',
                'details' => [
                    'steps_completed' => [],
                    'steps_failed' => ['migrate_fresh.py'],
                    'warnings' => ['Redis connection timeout'],
                ],
            ], 200),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);
        $result = $service->runFreshMigration();

        $this->assertFalse($result['success']);
        $this->assertEquals('Migration failed due to Redis connection error', $result['message']);
        $this->assertArrayHasKey('details', $result);
        $this->assertCount(1, $result['details']['steps_failed']);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function migration_only_works_correctly()
    {
        Http::fake([
            '*/migration/migrate-only' => Http::response([
                'success' => true,
                'message' => 'Migration completed successfully',
                'details' => [
                    'steps_completed' => ['migrate_fresh.py'],
                    'steps_failed' => [],
                    'warnings' => [],
                ],
            ], 200),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);
        $result = $service->runMigrationOnly();

        $this->assertTrue($result['success']);
        $this->assertEquals('Migration completed successfully', $result['message']);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function seeding_only_works_correctly()
    {
        Http::fake([
            '*/migration/seed-only' => Http::response([
                'success' => true,
                'message' => 'Seeding completed successfully',
                'details' => [
                    'steps_completed' => ['seed_data.py'],
                    'steps_failed' => [],
                    'warnings' => [],
                ],
            ], 200),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);
        $result = $service->runSeedingOnly();

        $this->assertTrue($result['success']);
        $this->assertEquals('Seeding completed successfully', $result['message']);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function get_status_returns_complete_status_information()
    {
        Http::fake([
            '*/migration/status' => Http::response([
                'debug_mode' => true,
                'migration_available' => true,
                'seeding_available' => true,
                'available_endpoints' => [
                    '/migration/fresh - Complete fresh migration with seeding',
                    '/migration/migrate-only - Migration without seeding',
                    '/migration/seed-only - Seeding without migration',
                    '/migration/status - This status endpoint',
                ],
                'environment' => [
                    'storage_type' => 'local',
                    'redis_host' => 'localhost',
                    'redis_port' => 6379,
                ],
            ], 200),
        ]);

        $service = app(AudioMicroserviceMigrationService::class);
        $result = $service->getStatus();

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('data', $result);
        $this->assertTrue($result['data']['debug_mode']);
        $this->assertTrue($result['data']['migration_available']);
        $this->assertTrue($result['data']['seeding_available']);
        $this->assertArrayHasKey('environment', $result['data']);
        $this->assertEquals('local', $result['data']['environment']['storage_type']);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function service_handles_connection_errors_gracefully()
    {
        // Mock HTTP timeout/connection error
        Http::fake([
            '*/migration/fresh' => function () {
                throw new \Exception('Connection refused');
            },
        ]);

        $service = app(AudioMicroserviceMigrationService::class);
        $result = $service->runFreshMigration();

        $this->assertFalse($result['success']);
    }
}
