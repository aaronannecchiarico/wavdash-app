<?php

namespace App\Console\Commands;

use App\Services\AudioMicroserviceMigrationService;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Storage;
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
        $defaultDisk = config('filesystems.default');

        if ($defaultDisk === 'r2') {
            // For R2 two-bucket system, clear buckets directly
            $this->clearR2Buckets();
        } else {
            // For local/other storage, clear traditional directory structure
            $this->clearLocalStorageDirectories();
        }
    }

    /**
     * Clear R2 buckets for two-bucket system
     */
    private function clearR2Buckets(): void
    {
        try {
            // Clear using direct R2 client
            $s3Client = new \Aws\S3\S3Client([
                'version' => 'latest',
                'region' => 'auto',
                'endpoint' => config('filesystems.disks.r2.endpoint'),
                'use_path_style_endpoint' => true,
                'credentials' => [
                    'key' => config('filesystems.disks.r2.key'),
                    'secret' => config('filesystems.disks.r2.secret'),
                ],
            ]);

            $clearedFiles = 0;

            // Clear audio-private bucket
            $privateBucket = config('filesystems.disks.r2.bucket', 'audio-private');
            $result = $s3Client->listObjectsV2(['Bucket' => $privateBucket]);
            if (isset($result['Contents']) && count($result['Contents']) > 0) {
                $objects = array_map(fn ($obj) => ['Key' => $obj['Key']], $result['Contents']);
                $s3Client->deleteObjects([
                    'Bucket' => $privateBucket,
                    'Delete' => ['Objects' => $objects],
                ]);
                $clearedFiles += count($objects);
                $this->line("  ✓ Cleared R2 private bucket ({$privateBucket}) - ".count($objects).' files');
            } else {
                $this->line("  ○ R2 private bucket ({$privateBucket}) already empty");
            }

            // Clear audio-public bucket
            $publicBucket = config('filesystems.disks.r2_public.bucket', 'audio-public');
            $result = $s3Client->listObjectsV2(['Bucket' => $publicBucket]);
            if (isset($result['Contents']) && count($result['Contents']) > 0) {
                $objects = array_map(fn ($obj) => ['Key' => $obj['Key']], $result['Contents']);
                $s3Client->deleteObjects([
                    'Bucket' => $publicBucket,
                    'Delete' => ['Objects' => $objects],
                ]);
                $clearedFiles += count($objects);
                $this->line("  ✓ Cleared R2 public bucket ({$publicBucket}) - ".count($objects).' files');
            } else {
                $this->line("  ○ R2 public bucket ({$publicBucket}) already empty");
            }

            if ($clearedFiles > 0) {
                $this->info("✅ R2 storage cleanup completed: {$clearedFiles} files removed from both buckets");
            } else {
                $this->info('✅ R2 buckets were already clean');
            }

        } catch (\Exception $e) {
            $this->warn("⚠️  Failed to clear R2 buckets: {$e->getMessage()}");
            $this->warn('Falling back to local storage cleanup...');
            $this->clearLocalStorageDirectories();
        }
    }

    /**
     * Clear local storage directories (traditional approach)
     */
    private function clearLocalStorageDirectories(): void
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
            // Use local disk specifically to avoid R2
            $disk = Storage::disk('local');

            if ($disk->exists($directory)) {
                $files = $disk->allFiles($directory);
                $totalFiles += count($files);

                if (count($files) > 0) {
                    $disk->deleteDirectory($directory);
                    $this->line("  ✓ Cleared {$directory} ({".count($files).'} files)');
                    $clearedCount++;
                } else {
                    $this->line("  ○ {$directory} already empty");
                }

                // Recreate the directory structure on local disk
                $disk->makeDirectory($directory);
            } else {
                $this->line("  ○ {$directory} does not exist, creating...");
                $disk->makeDirectory($directory);
            }
        }

        if ($totalFiles > 0) {
            $this->info("✅ Local storage cleanup completed: {$totalFiles} files removed from {$clearedCount} directories");
        } else {
            $this->info('✅ Local storage directories were already clean');
        }
    }
}
