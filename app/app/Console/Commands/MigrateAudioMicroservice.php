<?php

namespace App\Console\Commands;

use App\Services\AudioMicroserviceMigrationService;
use Illuminate\Console\Command;

class MigrateAudioMicroservice extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'audio:migrate 
                           {--type=fresh : Migration type (fresh, migrate-only, seed-only)}
                           {--force : Force migration without confirmation}
                           {--silent : Run without output for automated processes}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Trigger migrations on the audio processing microservice';

    public function __construct(
        private AudioMicroserviceMigrationService $migrationService
    ) {
        parent::__construct();
    }

    /**
     * Execute the console command.
     */
    public function handle(): int
    {
        $type = $this->option('type');
        $force = $this->option('force');
        $silent = $this->option('silent');

        if (! $silent) {
            $this->info('🎵 Audio Microservice Migration');
            $this->info("Type: {$type}");
            $this->newLine();
        }

        // Check if microservice is available
        if (! $this->migrationService->isAvailable()) {
            if (! $silent) {
                $this->error('❌ Audio microservice migration endpoints are not available.');
                $this->warn('💡 Ensure the microservice is running with DEBUG=true');
                $this->newLine();
                $this->line('To start the microservice in development mode:');
                $this->line('cd /path/to/beat-forge-audio-feature-extraction-service');
                $this->line('source beatforge-audio-extraction-service-local/bin/activate');
                $this->line('uvicorn main:app --reload --port 8001');
            }

            return Command::FAILURE;
        }

        // Show status first
        if (! $silent) {
            $this->showMigrationStatus();
        }

        // Confirm with user unless forced or silent
        if (! $force && ! $silent && $type === 'fresh') {
            if (! $this->confirm('⚠️  This will clear all microservice cache and task data. Continue?')) {
                $this->info('Migration cancelled.');

                return Command::SUCCESS;
            }
        }

        if (! $silent) {
            $this->info("🚀 Starting {$type} migration on audio microservice...");
            $this->newLine();
        }

        // Run appropriate migration
        $result = match ($type) {
            'fresh' => $this->migrationService->runFreshMigration(),
            'migrate-only' => $this->migrationService->runMigrationOnly(),
            'seed-only' => $this->migrationService->runSeedingOnly(),
            default => [
                'success' => false,
                'message' => "Invalid migration type: {$type}",
                'details' => [],
            ]
        };

        // Display results
        if ($result['success']) {
            if (! $silent) {
                $this->info("✅ {$result['message']}");
                $this->newLine();

                if (! empty($result['details']['steps_completed'])) {
                    $this->info('📋 Completed steps:');
                    foreach ($result['details']['steps_completed'] as $step) {
                        $this->line("  ✓ {$step}");
                    }
                    $this->newLine();
                }

                if (! empty($result['details']['warnings'])) {
                    $this->warn('⚠️  Warnings:');
                    foreach ($result['details']['warnings'] as $warning) {
                        $this->line("  ⚠ {$warning}");
                    }
                    $this->newLine();
                }
            }

            return Command::SUCCESS;
        } else {
            if (! $silent) {
                $this->error("❌ {$result['message']}");

                if (! empty($result['details']['steps_failed'])) {
                    $this->error('💥 Failed steps:');
                    foreach ($result['details']['steps_failed'] as $step) {
                        $this->line("  ✗ {$step}");
                    }
                }
            }

            return Command::FAILURE;
        }
    }

    /**
     * Show current migration status
     */
    private function showMigrationStatus(): void
    {
        $status = $this->migrationService->getStatus();

        if ($status['success']) {
            $data = $status['data'];

            $this->info('📊 Current Migration System Status:');
            $this->line('  Debug Mode: '.($data['debug_mode'] ? '✅ Enabled' : '❌ Disabled'));
            $this->line('  Migration Available: '.($data['migration_available'] ? '✅ Yes' : '❌ No'));
            $this->line('  Seeding Available: '.($data['seeding_available'] ? '✅ Yes' : '❌ No'));

            if (isset($data['environment'])) {
                $this->line("  Storage Type: {$data['environment']['storage_type']}");
                $this->line("  Redis: {$data['environment']['redis_host']}:{$data['environment']['redis_port']}");
            }

            $this->newLine();
        } else {
            $this->warn("⚠️  Could not retrieve migration status: {$status['message']}");
            $this->newLine();
        }
    }
}
