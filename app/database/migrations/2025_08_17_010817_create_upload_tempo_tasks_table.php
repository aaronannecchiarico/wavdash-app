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
        Schema::create('upload_tempo_tasks', function (Blueprint $table) {
            $table->id();
            $table->foreignId('upload_id')->constrained()->cascadeOnDelete();
            $table->string('task_id')->unique(); // External API task ID
            $table->string('status')->default('pending'); // pending, processing, completed, failed
            $table->text('error_message')->nullable();
            $table->integer('progress')->default(0); // 0-100
            $table->json('processing_options')->nullable(); // Store preset, tempo_factor, etc.
            $table->timestamp('submitted_at')->nullable();
            $table->timestamp('completed_at')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('upload_tempo_tasks');
    }
};
