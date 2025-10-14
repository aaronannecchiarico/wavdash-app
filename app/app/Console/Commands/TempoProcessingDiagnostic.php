<?php

namespace App\Console\Commands;

use App\Services\AudioMicroserviceClient;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Http;

class TempoProcessingDiagnostic extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'tempo:diagnostic';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Run diagnostic checks for tempo processing microservice';

    /**
     * Execute the console command.
     */
    public function handle(): int
    {
        $this->info('Running Tempo Processing Diagnostic...');
        $this->newLine();

        $client = new AudioMicroserviceClient;
        $baseUrl = config('services.audio_analysis.base_url', 'http://localhost:8001');

        // Check basic connectivity
        $this->info('1. Checking microservice connectivity...');
        try {
            $response = Http::timeout(5)->get($baseUrl.'/health');
            if ($response->successful()) {
                $health = $response->json();
                $this->info('   ✓ Microservice is healthy');
                $this->info("   ✓ Storage type: {$health['storage_type']}");
                $this->info("   ✓ Device: {$health['device_info']['optimal_device']}");
            } else {
                $this->error('   ✗ Microservice health check failed');

                return 1;
            }
        } catch (\Exception $e) {
            $this->error('   ✗ Cannot connect to microservice: '.$e->getMessage());

            return 1;
        }

        // Check tempo presets
        $this->newLine();
        $this->info('2. Checking tempo presets...');
        try {
            $presets = $client->getTempoPresets();
            $this->info('   ✓ Tempo presets available: '.count($presets['available_presets'] ?? []));
            foreach ($presets['available_presets'] ?? [] as $key => $preset) {
                $this->info("     - {$preset['name']} ({$key})");
            }
        } catch (\Exception $e) {
            $this->error('   ✗ Failed to get tempo presets: '.$e->getMessage());
        }

        // Check Celery workers
        $this->newLine();
        $this->info('3. Checking Celery worker status...');
        try {
            $response = Http::timeout(5)->get($baseUrl.'/health');
            $health = $response->json();
            if (isset($health['redis_connected']) && is_array($health['redis_connected']) && count($health['redis_connected']) > 0) {
                $this->info('   ✓ Celery workers connected');
                foreach ($health['redis_connected'] as $workers) {
                    if (is_array($workers)) {
                        foreach ($workers as $worker => $status) {
                            $this->info("     - {$worker}: {$status}");
                        }
                    }
                }
            } else {
                $this->error('   ✗ No Celery workers found');
            }
        } catch (\Exception $e) {
            $this->error('   ✗ Failed to check Celery status: '.$e->getMessage());
        }

        // Test tempo endpoint with minimal payload
        $this->newLine();
        $this->info('4. Testing tempo processing endpoint...');
        try {
            $response = Http::timeout(10)->asJson()->post($baseUrl.'/tempo/storage/process', [
                'storage_path' => 'test-file-that-does-not-exist.mp3',
                'preset_name' => 'sped_up',
            ]);

            if ($response->status() === 404 && str_contains($response->body(), 'File not found')) {
                $this->info('   ✓ Tempo endpoint is accessible (file not found error expected)');
            } else {
                $this->warning('   ⚠ Unexpected response from tempo endpoint:');
                $this->line('     Status: '.$response->status());
                $this->line('     Body: '.$response->body());
            }
        } catch (\Exception $e) {
            $this->error('   ✗ Tempo endpoint test failed: '.$e->getMessage());
        }

        $this->newLine();
        $this->info('Diagnostic complete.');
        $this->newLine();

        // Provide recommendations
        $this->info('Recommendations:');
        $this->info('- The error "\'function\' object has no attribute \'delay\'" suggests a Celery configuration issue');
        $this->info('- Check that tempo processing functions are properly decorated with @app.task in the microservice');
        $this->info('- Ensure Celery workers are running and properly configured for tempo processing tasks');
        $this->info('- Check the microservice logs for more detailed error information');

        return 0;
    }
}
