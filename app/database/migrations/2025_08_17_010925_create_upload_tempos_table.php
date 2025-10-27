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
        Schema::create('upload_tempos', function (Blueprint $table) {
            $table->id();
            $table->foreignId('upload_id')->constrained()->cascadeOnDelete();
            $table->string('preset'); // sped_up, slowed_reverb, nightcore, etc.
            $table->float('tempo_factor'); // Tempo multiplier (0.25-4.0)
            $table->float('pitch_shift_semitones')->nullable(); // Pitch shift in semitones
            $table->boolean('preserve_pitch')->default(false);
            $table->boolean('add_reverb')->default(false);
            $table->boolean('use_stems')->default(false);
            $table->string('file_path'); // Path to the processed tempo file
            $table->string('storage_type')->default('r2'); // local, r2, etc.
            $table->bigInteger('file_size')->nullable(); // File size in bytes
            $table->float('duration')->nullable(); // Duration in seconds
            $table->float('final_bpm')->nullable(); // Final BPM after processing
            $table->json('processing_metadata')->nullable(); // Additional processing metadata
            $table->timestamps();

            $table->index(['upload_id', 'preset']); // For finding tempo variations per upload
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('upload_tempos');
    }
};
