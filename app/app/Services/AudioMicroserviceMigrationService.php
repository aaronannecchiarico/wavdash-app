<?php

namespace App\Services;

use Exception;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AudioMicroserviceMigrationService
{
    private string $baseUrl;

    private int $timeout;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('services.audio_analysis.base_url', 'http://localhost:8001'), '/');
        $this->timeout = config('services.audio_analysis.migration_timeout', 300); // 5 minutes
    }

    /**
     * Check if migration endpoints are available
     */
    public function isAvailable(): bool
    {
        try {
            $response = Http::timeout(10)
                ->get("{$this->baseUrl}/migration/status");

            return $response->successful() && $response->json('debug_mode', false);
        } catch (Exception $e) {
            Log::warning('Audio microservice migration availability check failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl,
            ]);

            return false;
        }
    }

    /**
     * Get migration status from the microservice
     */
    public function getStatus(): array
    {
        try {
            $response = Http::timeout(10)
                ->get("{$this->baseUrl}/migration/status");

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json(),
                ];
            }

            return [
                'success' => false,
                'message' => 'Failed to get migration status',
                'details' => $response->body(),
            ];
        } catch (Exception $e) {
            Log::error('Migration status request failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl,
            ]);

            return [
                'success' => false,
                'message' => 'Failed to connect to microservice: '.$e->getMessage(),
                'details' => [],
            ];
        }
    }

    /**
     * Run complete fresh migration (migration + seeding)
     */
    public function runFreshMigration(): array
    {
        Log::info('Starting fresh migration on audio microservice', [
            'url' => $this->baseUrl,
        ]);

        try {
            $response = Http::timeout($this->timeout)
                ->post("{$this->baseUrl}/migration/fresh");

            $data = $response->json();

            if ($response->successful() && $data['success']) {
                Log::info('Fresh migration completed successfully', $data);

                return [
                    'success' => true,
                    'message' => $data['message'],
                    'details' => $data['details'],
                ];
            } else {
                Log::error('Fresh migration failed', $data);

                return [
                    'success' => false,
                    'message' => $data['message'] ?? 'Migration failed',
                    'details' => $data['details'] ?? [],
                ];
            }
        } catch (Exception $e) {
            Log::error('Fresh migration request failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl,
            ]);

            return [
                'success' => false,
                'message' => 'Failed to connect to microservice: '.$e->getMessage(),
                'details' => [],
            ];
        }
    }

    /**
     * Run migration only (without seeding)
     */
    public function runMigrationOnly(): array
    {
        Log::info('Starting migration-only on audio microservice', [
            'url' => $this->baseUrl,
        ]);

        try {
            $response = Http::timeout($this->timeout)
                ->post("{$this->baseUrl}/migration/migrate-only");

            $data = $response->json();

            if ($response->successful() && $data['success']) {
                Log::info('Migration-only completed successfully', $data);

                return [
                    'success' => true,
                    'message' => $data['message'],
                    'details' => $data['details'],
                ];
            } else {
                Log::error('Migration-only failed', $data);

                return [
                    'success' => false,
                    'message' => $data['message'] ?? 'Migration failed',
                    'details' => $data['details'] ?? [],
                ];
            }
        } catch (Exception $e) {
            Log::error('Migration-only request failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl,
            ]);

            return [
                'success' => false,
                'message' => 'Failed to connect to microservice: '.$e->getMessage(),
                'details' => [],
            ];
        }
    }

    /**
     * Run seeding only (without migration)
     */
    public function runSeedingOnly(): array
    {
        Log::info('Starting seeding-only on audio microservice', [
            'url' => $this->baseUrl,
        ]);

        try {
            $response = Http::timeout($this->timeout)
                ->post("{$this->baseUrl}/migration/seed-only");

            $data = $response->json();

            if ($response->successful() && $data['success']) {
                Log::info('Seeding-only completed successfully', $data);

                return [
                    'success' => true,
                    'message' => $data['message'],
                    'details' => $data['details'],
                ];
            } else {
                Log::error('Seeding-only failed', $data);

                return [
                    'success' => false,
                    'message' => $data['message'] ?? 'Seeding failed',
                    'details' => $data['details'] ?? [],
                ];
            }
        } catch (Exception $e) {
            Log::error('Seeding-only request failed', [
                'error' => $e->getMessage(),
                'url' => $this->baseUrl,
            ]);

            return [
                'success' => false,
                'message' => 'Failed to connect to microservice: '.$e->getMessage(),
                'details' => [],
            ];
        }
    }
}
