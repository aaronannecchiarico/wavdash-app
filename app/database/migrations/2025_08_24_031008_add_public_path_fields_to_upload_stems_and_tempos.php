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
        Schema::table('upload_stems', function (Blueprint $table) {
            $table->string('public_path')->nullable()->after('file_path');
            $table->boolean('converted_to_ogg')->default(false)->after('storage_type');
        });

        Schema::table('upload_tempos', function (Blueprint $table) {
            $table->string('public_path')->nullable()->after('file_path');
            $table->boolean('converted_to_ogg')->default(false)->after('storage_type');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('upload_stems', function (Blueprint $table) {
            $table->dropColumn(['public_path', 'converted_to_ogg']);
        });

        Schema::table('upload_tempos', function (Blueprint $table) {
            $table->dropColumn(['public_path', 'converted_to_ogg']);
        });
    }
};
