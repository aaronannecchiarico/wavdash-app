<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('upload_stems', function (Blueprint $table) {
            $table->id();
            $table->foreignId('upload_id')->constrained()->cascadeOnDelete();
            $table->string('stem_type'); // vocals, drums, bass, other
            $table->string('file_path'); // Path to the separated stem file
            $table->string('storage_type')->default('r2'); // local, r2, etc.
            $table->bigInteger('file_size')->nullable(); // File size in bytes
            $table->float('duration')->nullable(); // Duration in seconds
            $table->json('metadata')->nullable(); // Additional metadata
            $table->timestamps();

            $table->unique(['upload_id', 'stem_type']); // Prevent duplicate stem types per upload
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('upload_stems');
    }
};
