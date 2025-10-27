<?php

namespace App\Console\Commands;

use App\Models\UploadTempoTask;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;

class FixCompletedTempoTasks extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'tempo:fix-completed-tasks';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Create missing UploadTempo records for completed tempo tasks';

    /**
     * Execute the console command.
     */
    public function handle(): int
    {
        $this->info('Finding completed tempo tasks without corresponding tempo records...');

        $tasks = UploadTempoTask::with('upload')
            ->where('status', 'completed')
            ->whereDoesntHave('upload.tempos')
            ->get();

        if ($tasks->isEmpty()) {
            $this->info('No completed tempo tasks found that need fixing.');

            return Command::SUCCESS;
        }

        $this->info("Found {$tasks->count()} completed tempo tasks without tempo records.");

        foreach ($tasks as $task) {
            $this->info("Processing task {$task->task_id} for upload '{$task->upload->title}'...");

            try {
                /** @var array<string, mixed> $options */
                $options = $task->processing_options ?? [];

                // Simulate the file path that would have been created
                $filePath = 'processed/1/'.date('Y/m/d', strtotime($task->completed_at)).'/'.
                           pathinfo($task->upload->filename, PATHINFO_FILENAME).'_tempo_'.
                           ($options['preset'] ?? 'custom').'_'.($options['tempo_factor'] ?? '1.0').'.wav';

                $task->upload->tempos()->create([
                    'preset' => $options['preset'] ?? 'custom',
                    'tempo_factor' => (float) ($options['tempo_factor'] ?? 1.0),
                    'pitch_shift_semitones' => (float) ($options['pitch_shift_semitones'] ?? 0.0),
                    'preserve_pitch' => (bool) ($options['preserve_pitch'] ?? false),
                    'add_reverb' => (bool) ($options['add_reverb'] ?? false),
                    'use_stems' => (bool) ($options['use_stems'] ?? false),
                    'file_path' => $filePath,
                    'storage_type' => 'local', // Assume local for existing files
                    'file_size' => null,
                    'duration' => $task->upload->duration_seconds,
                    'final_bpm' => null,
                    'processing_metadata' => [
                        'task_id' => $task->task_id,
                        'restored_from_task' => true,
                        'task_options' => $options,
                    ],
                ]);

                $this->info("✓ Created tempo record for task {$task->task_id}");

            } catch (\Exception $e) {
                $this->error("✗ Failed to create tempo record for task {$task->task_id}: {$e->getMessage()}");
                Log::error('Failed to fix tempo task', [
                    'task_id' => $task->task_id,
                    'error' => $e->getMessage(),
                ]);
            }
        }

        $this->info('Completed fixing tempo tasks.');

        return Command::SUCCESS;
    }
}
