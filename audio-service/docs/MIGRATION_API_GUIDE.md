# Migration API Guide

This guide explains how to trigger fresh migrations in the Audio Processing Microservice from Laravel via API endpoints, specifically for development and local environments.

## Overview

The microservice provides REST API endpoints that allow Laravel to trigger fresh migrations remotely. These endpoints are **only available in development environments** where `DEBUG=true` is set.

## Security & Environment Protection

### Environment Restriction
All migration endpoints are protected by environment checks:
- ✅ **Available**: When `DEBUG=true` (development/local)
- ❌ **Blocked**: When `DEBUG=false` (staging/production)

### Response for Protected Environments
```json
{
  "detail": "Migration endpoints are only available in development environments (DEBUG=true)"
}
```

## Available Endpoints

### Base URL
```
http://localhost:8001/migration
```

### 1. Complete Fresh Migration
**Endpoint**: `POST /migration/fresh`

Performs complete system reset:
- Clears Redis task tracking data
- Clears performance cache
- Initializes storage directories
- Seeds system with default data
- Validates setup

**Example Response**:
```json
{
  "success": true,
  "message": "Fresh migration and seeding completed successfully",
  "details": {
    "steps_completed": ["migrate_fresh.py", "seed_data.py"],
    "steps_failed": [],
    "warnings": [],
    "migrate_fresh_output": "🎉 Fresh migration completed successfully!...",
    "seed_data_output": "🌱 Data seeding completed successfully!..."
  }
}
```

### 2. Migration Only (No Seeding)
**Endpoint**: `POST /migration/migrate-only`

Runs only the migration step without seeding default data.

### 3. Seeding Only (No Migration)
**Endpoint**: `POST /migration/seed-only`

Seeds system with default data without clearing existing data.

### 4. Migration Status
**Endpoint**: `GET /migration/status`

Returns current migration system status and available operations.

**Example Response**:
```json
{
  "debug_mode": true,
  "migration_available": true,
  "seeding_available": true,
  "available_endpoints": [
    "/migration/fresh - Complete fresh migration with seeding",
    "/migration/migrate-only - Migration without seeding",
    "/migration/seed-only - Seeding without migration",
    "/migration/status - This status endpoint"
  ],
  "environment": {
    "storage_type": "local",
    "redis_host": "localhost",
    "redis_port": 6379
  }
}
```

## Laravel Integration

### Environment Setup

Ensure your microservice `.env` file has:
```bash
# Required for migration endpoints
DEBUG=true

# Storage configuration (must match Laravel)
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage  # Should point to shared storage with Laravel

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Laravel Configuration

Add microservice configuration to your Laravel `.env`:
```bash
# Audio Microservice Configuration
AUDIO_MICROSERVICE_URL=http://localhost:8001
AUDIO_MICROSERVICE_TIMEOUT=300  # 5 minutes for migrations
```

### Laravel Service Class

Create a service class to handle microservice migrations:

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Exception;

class AudioMicroserviceMigrationService
{
    private string $baseUrl;
    private int $timeout;

    public function __construct()
    {
        $this->baseUrl = config('services.audio_microservice.url', 'http://localhost:8001');
        $this->timeout = config('services.audio_microservice.timeout', 300);
    }

    /**
     * Check if migration endpoints are available
     */
    public function isAvailable(): bool
    {
        try {
            $response = Http::timeout($this->timeout)
                ->get("{$this->baseUrl}/migration/status");
            
            return $response->successful() && $response->json('debug_mode', false);
        } catch (Exception $e) {
            Log::error('Audio microservice migration availability check failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl
            ]);
            return false;
        }
    }

    /**
     * Run complete fresh migration (migration + seeding)
     */
    public function runFreshMigration(): array
    {
        Log::info('Starting fresh migration on audio microservice');

        try {
            $response = Http::timeout($this->timeout)
                ->post("{$this->baseUrl}/migration/fresh");

            $data = $response->json();

            if ($response->successful() && $data['success']) {
                Log::info('Fresh migration completed successfully', $data);
                return [
                    'success' => true,
                    'message' => $data['message'],
                    'details' => $data['details']
                ];
            } else {
                Log::error('Fresh migration failed', $data);
                return [
                    'success' => false,
                    'message' => $data['message'] ?? 'Migration failed',
                    'details' => $data['details'] ?? []
                ];
            }
        } catch (Exception $e) {
            Log::error('Fresh migration request failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl
            ]);
            
            return [
                'success' => false,
                'message' => 'Failed to connect to microservice: ' . $e->getMessage(),
                'details' => []
            ];
        }
    }

    /**
     * Run migration only (without seeding)
     */
    public function runMigrationOnly(): array
    {
        Log::info('Starting migration-only on audio microservice');

        try {
            $response = Http::timeout($this->timeout)
                ->post("{$this->baseUrl}/migration/migrate-only");

            $data = $response->json();

            if ($response->successful() && $data['success']) {
                Log::info('Migration-only completed successfully', $data);
                return [
                    'success' => true,
                    'message' => $data['message'],
                    'details' => $data['details']
                ];
            } else {
                Log::error('Migration-only failed', $data);
                return [
                    'success' => false,
                    'message' => $data['message'] ?? 'Migration failed',
                    'details' => $data['details'] ?? []
                ];
            }
        } catch (Exception $e) {
            Log::error('Migration-only request failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl
            ]);
            
            return [
                'success' => false,
                'message' => 'Failed to connect to microservice: ' . $e->getMessage(),
                'details' => []
            ];
        }
    }

    /**
     * Run seeding only (without migration)
     */
    public function runSeedingOnly(): array
    {
        Log::info('Starting seeding-only on audio microservice');

        try {
            $response = Http::timeout($this->timeout)
                ->post("{$this->baseUrl}/migration/seed-only");

            $data = $response->json();

            if ($response->successful() && $data['success']) {
                Log::info('Seeding-only completed successfully', $data);
                return [
                    'success' => true,
                    'message' => $data['message'],
                    'details' => $data['details']
                ];
            } else {
                Log::error('Seeding-only failed', $data);
                return [
                    'success' => false,
                    'message' => $data['message'] ?? 'Seeding failed',
                    'details' => $data['details'] ?? []
                ];
            }
        } catch (Exception $e) {
            Log::error('Seeding-only request failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl
            ]);
            
            return [
                'success' => false,
                'message' => 'Failed to connect to microservice: ' . $e->getMessage(),
                'details' => []
            ];
        }
    }
}
```

### Laravel Artisan Command

Create an Artisan command to trigger microservice migrations:

```php
<?php

namespace App\Console\Commands;

use App\Services\AudioMicroserviceMigrationService;
use Illuminate\Console\Command;

class MigrateAudioMicroservice extends Command
{
    protected $signature = 'audio:migrate 
                           {--type=fresh : Migration type (fresh, migrate-only, seed-only)}
                           {--force : Force migration without confirmation}';

    protected $description = 'Trigger migrations on the audio processing microservice';

    public function __construct(
        private AudioMicroserviceMigrationService $migrationService
    ) {
        parent::__construct();
    }

    public function handle(): int
    {
        $type = $this->option('type');
        $force = $this->option('force');

        // Check if microservice is available
        if (!$this->migrationService->isAvailable()) {
            $this->error('Audio microservice migration endpoints are not available.');
            $this->error('Ensure the microservice is running with DEBUG=true');
            return Command::FAILURE;
        }

        // Confirm with user unless forced
        if (!$force && $type === 'fresh') {
            if (!$this->confirm('This will clear all microservice cache and task data. Continue?')) {
                $this->info('Migration cancelled.');
                return Command::SUCCESS;
            }
        }

        $this->info("Starting {$type} migration on audio microservice...");

        // Run appropriate migration
        $result = match($type) {
            'fresh' => $this->migrationService->runFreshMigration(),
            'migrate-only' => $this->migrationService->runMigrationOnly(),
            'seed-only' => $this->migrationService->runSeedingOnly(),
            default => [
                'success' => false,
                'message' => "Invalid migration type: {$type}",
                'details' => []
            ]
        };

        // Display results
        if ($result['success']) {
            $this->info("✅ {$result['message']}");
            
            if (!empty($result['details']['steps_completed'])) {
                $this->info('Completed steps:');
                foreach ($result['details']['steps_completed'] as $step) {
                    $this->line("  ✓ {$step}");
                }
            }
            
            if (!empty($result['details']['warnings'])) {
                $this->warn('Warnings:');
                foreach ($result['details']['warnings'] as $warning) {
                    $this->line("  ⚠ {$warning}");
                }
            }
            
            return Command::SUCCESS;
        } else {
            $this->error("❌ {$result['message']}");
            
            if (!empty($result['details']['steps_failed'])) {
                $this->error('Failed steps:');
                foreach ($result['details']['steps_failed'] as $step) {
                    $this->line("  ✗ {$step}");
                }
            }
            
            return Command::FAILURE;
        }
    }
}
```

### Laravel Migration Integration

Call microservice migration from your Laravel migrations:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use App\Services\AudioMicroserviceMigrationService;

return new class extends Migration
{
    public function up()
    {
        // Your regular Laravel migration code here
        
        // Trigger microservice migration if available
        $migrationService = app(AudioMicroserviceMigrationService::class);
        
        if ($migrationService->isAvailable()) {
            \Log::info('Triggering audio microservice fresh migration');
            $result = $migrationService->runFreshMigration();
            
            if (!$result['success']) {
                \Log::warning('Audio microservice migration failed', $result);
                // Note: Don't fail Laravel migration if microservice fails
            }
        }
    }
};
```

## Usage Examples

### Via Artisan Command
```bash
# Fresh migration (with confirmation)
php artisan audio:migrate --type=fresh

# Fresh migration (forced, no confirmation)
php artisan audio:migrate --type=fresh --force

# Migration only
php artisan audio:migrate --type=migrate-only

# Seeding only
php artisan audio:migrate --type=seed-only
```

### Via Service Class
```php
$migrationService = app(AudioMicroserviceMigrationService::class);

// Check availability
if ($migrationService->isAvailable()) {
    // Run fresh migration
    $result = $migrationService->runFreshMigration();
    
    if ($result['success']) {
        // Handle success
        \Log::info('Microservice migration successful');
    } else {
        // Handle failure
        \Log::error('Microservice migration failed', $result);
    }
}
```

### Direct HTTP Calls
```bash
# Check status
curl -X GET http://localhost:8001/migration/status

# Run fresh migration
curl -X POST http://localhost:8001/migration/fresh

# Migration only
curl -X POST http://localhost:8001/migration/migrate-only

# Seeding only
curl -X POST http://localhost:8001/migration/seed-only
```

## Best Practices

### 1. Environment Safety
- Always verify `DEBUG=true` before enabling migration endpoints
- Never expose migration endpoints in production
- Use separate configuration for different environments

### 2. Error Handling
- Always check microservice availability before calling migration endpoints
- Handle timeouts gracefully (migrations can take several minutes)
- Log all migration attempts and results
- Don't fail Laravel migrations if microservice migrations fail

### 3. Coordination
- Run microservice migrations after Laravel migrations
- Ensure shared storage paths are properly configured
- Coordinate Redis cleanup timing if sharing Redis instances

### 4. Monitoring
- Monitor migration execution time
- Log detailed migration results
- Set up alerts for migration failures
- Track migration frequency in development

## Troubleshooting

### Common Issues

1. **403 Forbidden**: `DEBUG=false` in microservice environment
2. **Connection Failed**: Microservice not running or wrong URL
3. **Timeout**: Migration taking longer than configured timeout
4. **Script Not Found**: Migration scripts missing from microservice

### Debugging Steps

1. Check microservice logs: `tail -f logs/microservice.log`
2. Verify microservice status: `curl http://localhost:8001/health`
3. Check migration endpoint status: `curl http://localhost:8001/migration/status`
4. Verify environment variables in microservice `.env`
5. Ensure shared storage paths match between Laravel and microservice

### Log Locations

- **Laravel Logs**: `storage/logs/laravel.log`
- **Microservice Logs**: `logs/microservice.log`
- **Migration Script Logs**: Console output captured in API responses

## Security Considerations

1. **Environment Protection**: Migration endpoints automatically blocked in production
2. **Local Network Only**: Endpoints should only be accessible from trusted networks
3. **No Authentication**: Relies on environment protection and network security
4. **Audit Logging**: All migration attempts are logged with timestamps
5. **Data Loss Warning**: Fresh migrations clear all cached data and task history

---

**⚠️ Important**: These migration endpoints are designed for development workflows only. They provide direct system access and should never be exposed in production environments.