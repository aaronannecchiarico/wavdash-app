<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        // Clean up any duplicate tasks before adding the constraint.
        // MySQL does not allow referencing the target table directly in a
        // DELETE subquery (error 1093). Wrapping the subquery in a derived
        // table alias works on both MySQL and SQLite.
        DB::statement('
            DELETE FROM upload_tempo_tasks
            WHERE id IN (
                SELECT id FROM (
                    SELECT t1.id
                    FROM upload_tempo_tasks t1
                    INNER JOIN upload_tempo_tasks t2
                        ON t1.upload_id = t2.upload_id AND t1.id > t2.id
                ) AS duplicates
            )
        ');

        Schema::table('upload_tempo_tasks', function (Blueprint $table) {
            // Add unique constraint to prevent multiple active tasks per upload
            $table->unique('upload_id', 'unique_upload_tempo_task');

            // Also add an index on task_id for faster lookups in the callback handler
            $table->index('task_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('upload_tempo_tasks', function (Blueprint $table) {
            $table->dropUnique('unique_upload_tempo_task');
            $table->dropIndex(['task_id']);
        });
    }
};
