<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('upload_stem_tasks', function (Blueprint $table) {
            $table->string('model_name')->nullable()->after('task_id');
        });
    }

    public function down(): void
    {
        Schema::table('upload_stem_tasks', function (Blueprint $table) {
            $table->dropColumn('model_name');
        });
    }
};
