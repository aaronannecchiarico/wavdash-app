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
        Schema::create('upload_analyses', function (Blueprint $table) {
            $table->id();
            $table->foreignId('upload_id')->constrained()->cascadeOnDelete();

            // Musical Analysis Data - Core Fields from API Integration Guide
            $table->string('musical_key')->nullable(); // "E major", "A minor"
            $table->float('key_confidence')->nullable(); // 0.0 - 1.0
            $table->integer('bpm')->nullable(); // Rounded BPM value
            $table->float('beat_regularity')->nullable(); // 0.0 - 1.0 rhythm consistency
            $table->float('loudness_db')->nullable(); // Overall loudness in dB
            $table->float('dynamic_range_db')->nullable(); // Compression level indicator
            $table->float('brightness')->nullable(); // Spectral centroid (Hz)
            $table->float('timbral_complexity')->nullable(); // Texture complexity

            // Processing Metadata
            $table->float('analysis_duration')->nullable(); // Analysis processing time
            $table->integer('chunk_count')->nullable(); // Processing segments
            $table->integer('key_changes')->default(1); // Key modulations detected

            $table->timestamps();

            // Add index on upload_id for faster lookups
            $table->index('upload_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('upload_analyses');
    }
};
