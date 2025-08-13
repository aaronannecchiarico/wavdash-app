<?php

namespace App\Console\Commands;

use App\Models\Upload;
use App\Services\R2StorageService;
use Illuminate\Console\Command;

class MigrateUploadsToR2 extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'uploads:migrate-to-r2 {--dry-run : Show what would be migrated without making changes} {--limit=10 : Number of uploads to process}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Migrate existing local uploads to Cloudflare R2 storage';

    /**
     * Execute the console command.
     */
    public function handle(R2StorageService $r2Service)
    {
        if (!$r2Service->isEnabled()) {
            $this->error('R2 storage is not enabled. Please configure R2 settings in your .env file.');
            return self::FAILURE;
        }

        $dryRun = $this->option('dry-run');
        $limit = (int) $this->option('limit');

        $this->info('Starting upload migration to R2...');
        
        if ($dryRun) {
            $this->warn('DRY RUN MODE - No changes will be made');
        }

        // Get uploads that are not using R2 storage
        $uploads = Upload::where('uses_r2_storage', false)
            ->whereNotNull('path')
            ->where('status', 'ready')
            ->limit($limit)
            ->get();

        if ($uploads->isEmpty()) {
            $this->info('No uploads found that need migration.');
            return self::SUCCESS;
        }

        $this->info("Found {$uploads->count()} uploads to migrate.");

        $progressBar = $this->output->createProgressBar($uploads->count());
        $progressBar->start();

        $successCount = 0;
        $failureCount = 0;

        foreach ($uploads as $upload) {
            try {
                if ($dryRun) {
                    $this->line("\nWould migrate: {$upload->title} (ID: {$upload->id})");
                    $successCount++;
                } else {
                    if ($r2Service->migrateUpload($upload)) {
                        $successCount++;
                        $this->line("\n✓ Migrated: {$upload->title}");
                    } else {
                        $failureCount++;
                        $this->line("\n✗ Failed: {$upload->title}");
                    }
                }
            } catch (\Exception $e) {
                $failureCount++;
                $this->line("\n✗ Error migrating {$upload->title}: {$e->getMessage()}");
            }

            $progressBar->advance();
        }

        $progressBar->finish();

        $this->newLine(2);
        $this->info("Migration completed!");
        $this->info("Successful: {$successCount}");
        if ($failureCount > 0) {
            $this->error("Failed: {$failureCount}");
        }

        if ($dryRun) {
            $this->warn('This was a dry run. Use --dry-run=false to perform actual migration.');
        }

        return self::SUCCESS;
    }
}