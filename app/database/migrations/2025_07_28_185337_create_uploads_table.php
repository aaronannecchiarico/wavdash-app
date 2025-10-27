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
        Schema::create('uploads', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('title');
            $table->text('description')->nullable();
            $table->string('genre')->nullable();
            $table->string('filename');
            $table->string('path'); // Original file path
            $table->string('stream_path')->nullable(); // Web-friendly version for playback
            $table->string('mime_type');
            $table->bigInteger('size'); // File size in bytes
            $table->string('status')->default('pending'); // pending, processing, ready, failed
            $table->integer('duration_seconds')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        // Clear all upload storage before dropping the table
        $this->clearUploadStorage();

        Schema::dropIfExists('uploads');
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
