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
        Schema::table('contest_users', function (Blueprint $table) {
            // Add the upload_id foreign key
            $table->foreignId('upload_id')->nullable()->after('contest_id');
            $table->foreign('upload_id')->references('id')->on('uploads')->nullOnDelete();

            // Make original_path and streamable_path nullable since they'll now come from the upload
            $table->string('original_path')->nullable()->change();
            $table->string('streamable_path')->nullable()->change();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('contest_users', function (Blueprint $table) {
            // Remove the foreign key constraint
            $table->dropForeign(['upload_id']);
            $table->dropColumn('upload_id');

            // Make the original fields required again
            $table->string('original_path')->nullable(false)->change();
        });
    }
};
