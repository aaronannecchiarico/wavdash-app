<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\Storage;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('uploads', function (Blueprint $table) {
            $table->string('r2_upload_path')->nullable()->after('stream_path');
            $table->json('r2_stems_paths')->nullable()->after('r2_upload_path');
            $table->string('r2_analysis_path')->nullable()->after('r2_stems_paths');
            $table->timestamp('r2_uploaded_at')->nullable()->after('r2_analysis_path');
            $table->boolean('uses_r2_storage')->default(false)->after('r2_uploaded_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        // Clean up any remaining upload files before dropping columns
        $this->clearUploadStorage();

        Schema::table('uploads', function (Blueprint $table) {
            $table->dropColumn([
                'r2_upload_path',
                'r2_stems_paths',
                'r2_analysis_path',
                'r2_uploaded_at',
                'uses_r2_storage',
            ]);
        });
    }

    /**
     * Clear all upload-related files from storage.
     */
    private function clearUploadStorage(): void
    {
        // Clear private uploads
        if (Storage::disk('private')->exists('uploads')) {
            Storage::disk('private')->deleteDirectory('uploads');
        }

        // Clear public uploads/stream
        if (Storage::disk('public')->exists('uploads/stream')) {
            Storage::disk('public')->deleteDirectory('uploads/stream');
        }

        // Clear R2 uploads if configured
        if (config('filesystems.disks.r2.bucket')) {
            try {
                if (Storage::disk('r2')->exists('uploads')) {
                    Storage::disk('r2')->deleteDirectory('uploads');
                }
                if (Storage::disk('r2')->exists('processed')) {
                    Storage::disk('r2')->deleteDirectory('processed');
                }
            } catch (\Exception $e) {
                // Ignore R2 errors during migration rollback
            }
        }
    }
};
