<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Storage;

class ClearUploadStorage extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'uploads:clear {--force : Force cleanup without confirmation}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Clear all upload-related files from storage (private, public, and R2)';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        if (!$this->option('force') && !$this->confirm('This will permanently delete all upload files. Are you sure?')) {
            $this->info('Operation cancelled.');
            return 0;
        }

        $this->info('Clearing upload storage...');

        $clearedCount = 0;

        // Clear private uploads
        if (Storage::disk('private')->exists('uploads')) {
            Storage::disk('private')->deleteDirectory('uploads');
            $this->info('✓ Cleared private uploads');
            $clearedCount++;
        }

        // Clear public uploads/stream
        if (Storage::disk('public')->exists('uploads')) {
            Storage::disk('public')->deleteDirectory('uploads');
            $this->info('✓ Cleared public uploads');
            $clearedCount++;
        }

        // Clear R2 uploads if configured
        if (config('filesystems.disks.r2.bucket')) {
            try {
                if (Storage::disk('r2')->exists('uploads')) {
                    Storage::disk('r2')->deleteDirectory('uploads');
                    $this->info('✓ Cleared R2 uploads');
                    $clearedCount++;
                }
                if (Storage::disk('r2')->exists('processed')) {
                    Storage::disk('r2')->deleteDirectory('processed');
                    $this->info('✓ Cleared R2 processed files');
                    $clearedCount++;
                }
            } catch (\Exception $e) {
                $this->warn('⚠ Could not clear R2 storage: ' . $e->getMessage());
            }
        }

        if ($clearedCount === 0) {
            $this->info('No upload files found to clear.');
        } else {
            $this->info("✓ Upload storage cleared successfully! ({$clearedCount} locations)");
        }

        return 0;
    }
}
