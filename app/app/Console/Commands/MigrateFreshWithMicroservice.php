<?php

namespace App\Console\Commands;

use App\Services\AudioMicroserviceMigrationService;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\DB;
use Symfony\Component\Console\Input\InputOption;

class MigrateFreshWithMicroservice extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'migrate:fresh-with-microservice
                           {--seed : Seed the database after migration}
                           {--seeder= : The class name of the root seeder}
                           {--force : Force the operation to run when in production}
                           {--skip-microservice : Skip microservice migration}
                           {--microservice-only : Only run microservice migration}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Drop all tables, clear storage, re-run migrations, and clean up microservice (ideal for development)';

    public function __construct(
        private AudioMicroserviceMigrationService $migrationService
    ) {
        parent::__construct();
    }

    /**
     * Configure the command.
     */
    protected function configure(): void
    {
        $this->setAliases(['migrate:fresh-all', 'migrate:fresh-complete']);
    }

    /**
     * Execute the console command.
     */
    public function handle(): int
    {
        $seed = $this->option('seed');
        $seeder = $this->option('seeder');
        $force = $this->option('force');
        $skipMicroservice = $this->option('skip-microservice');
        $microserviceOnly = $this->option('microservice-only');

        $this->info('🚀 Beat Forge - Complete Fresh Migration');
        $this->line('This will reset Laravel database, clear all storage, and clean up microservice');
        $this->newLine();

        // Environment safety check
        if (! $force && app()->environment('production')) {
            $this->error('❌ This command cannot be run in production without --force flag');

            return Command::FAILURE;
        }

        // Confirm in production or when not forced
        if (! $force && (app()->environment('production') || ! app()->environment('local'))) {
            if (! $this->confirm('⚠️  Are you sure you want to reset the entire system?')) {
                $this->info('Operation cancelled.');

                return Command::SUCCESS;
            }
        }

        // Step 1: Clean up microservice first (if not skipped)
        if (! $skipMicroservice) {
            $this->info('🎵 Step 1: Cleaning up audio microservice...');

            if ($this->migrationService->isAvailable()) {
                $result = $this->migrationService->runFreshMigration();

                if ($result['success']) {
                    $this->info("✅ Microservice: {$result['message']}");

                    if (! empty($result['details']['steps_completed'])) {
                        foreach ($result['details']['steps_completed'] as $step) {
                            $this->line("  ✓ {$step}");
                        }
                    }
                } else {
                    $this->warn("⚠️  Microservice migration failed: {$result['message']}");
                    $this->warn('Continuing with Laravel migration...');
                }
            } else {
                $this->warn('⚠️  Audio microservice is not available for migration');
                $this->warn('Continuing with Laravel migration...');
            }

            $this->newLine();
        }

        // If microservice-only flag is set, stop here
        if ($microserviceOnly) {
            $this->info('✅ Microservice-only migration completed');

            return Command::SUCCESS;
        }

        // Step 2: Clear Laravel storage directories
        $this->info('🗂️  Step 2: Clearing storage directories...');
        $this->clearStorageDirectories();
        $this->newLine();

        // Step 3: Run Laravel migrate:fresh
        $this->info('🗄️  Step 3: Running Laravel migrate:fresh...');

        $migrateCommand = ['migrate:fresh'];
        if ($force) {
            $migrateCommand[] = '--force';
        }

        $exitCode = $this->call('migrate:fresh', array_filter([
            '--force' => $force,
        ]));

        if ($exitCode !== 0) {
            $this->error('❌ Laravel migration failed');

            return Command::FAILURE;
        }

        $this->info('✅ Laravel migration completed');
        $this->newLine();

        // Step 4: Run seeding if requested
        if ($seed) {
            $this->info('🌱 Step 4: Seeding database...');

            $seedCommand = array_filter([
                '--force' => $force,
                '--class' => $seeder,
            ]);

            $exitCode = $this->call('db:seed', $seedCommand);

            if ($exitCode !== 0) {
                $this->error('❌ Database seeding failed');

                return Command::FAILURE;
            }

            $this->info('✅ Database seeding completed');
            $this->newLine();
        }

        // Step 5: Final status check
        $this->info('📊 Final System Status:');

        // Check Laravel database
        try {
            $tables = DB::select('SELECT name FROM sqlite_master WHERE type="table" AND name NOT LIKE "sqlite_%"');
            $this->line('  Database Tables: '.count($tables).' tables created');
        } catch (\Exception $e) {
            $this->line('  Database: ✅ Connected');
        }

        // Check microservice status
        if (! $skipMicroservice && $this->migrationService->isAvailable()) {
            $status = $this->migrationService->getStatus();
            if ($status['success']) {
                $data = $status['data'];
                $this->line('  Microservice: ✅ Available (Debug: '.($data['debug_mode'] ? 'On' : 'Off').')');
            } else {
                $this->line('  Microservice: ⚠️  Status unknown');
            }
        } elseif (! $skipMicroservice) {
            $this->line('  Microservice: ❌ Not available');
        }

        $this->newLine();
        $this->info('🎉 Complete fresh migration finished successfully!');

        if (! $skipMicroservice) {
            $this->newLine();
            $this->line('💡 Next steps:');
            $this->line('  • Upload some audio files to test the system');
            $this->line('  • Check microservice logs if needed');
            $this->line('  • Ensure Redis is running for task processing');
        }

        return Command::SUCCESS;
    }

    /**
     * Get the console command arguments.
     */
    protected function getArguments(): array
    {
        return [];
    }

    /**
     * Get the console command options.
     */
    protected function getOptions(): array
    {
        return [
            ['seed', null, InputOption::VALUE_NONE, 'Seed the database after migration'],
            ['seeder', null, InputOption::VALUE_OPTIONAL, 'The class name of the root seeder'],
            ['force', null, InputOption::VALUE_NONE, 'Force the operation to run when in production'],
            ['skip-microservice', null, InputOption::VALUE_NONE, 'Skip microservice migration'],
            ['microservice-only', null, InputOption::VALUE_NONE, 'Only run microservice migration'],
        ];
    }

    /**
     * Clear storage directories for uploads, processed files, and stems
     */
    private function clearStorageDirectories(): void
    {
        $directories = [
            'private/uploads',
            'private/processed',
            'private/stems',
            'public/uploads/stream',
        ];

        $clearedCount = 0;
        $totalFiles = 0;

        foreach ($directories as $directory) {
            if (Storage::exists($directory)) {
                $files = Storage::allFiles($directory);
                $totalFiles += count($files);

                if (count($files) > 0) {
                    Storage::deleteDirectory($directory);
                    $this->line("  ✓ Cleared {$directory} ({".count($files).'} files)');
                    $clearedCount++;
                } else {
                    $this->line("  ○ {$directory} already empty");
                }

                // Recreate the directory structure
                Storage::makeDirectory($directory);
            } else {
                $this->line("  ○ {$directory} does not exist, creating...");
                Storage::makeDirectory($directory);
            }
        }

        if ($totalFiles > 0) {
            $this->info("✅ Storage cleanup completed: {$totalFiles} files removed from {$clearedCount} directories");
        } else {
            $this->info('✅ Storage directories were already clean');
        }
    }
}
