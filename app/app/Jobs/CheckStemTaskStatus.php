<?php

namespace App\Jobs;

use App\Models\UploadStemTask;
use App\Services\AudioAnalysisService;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class CheckStemTaskStatus implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    /**
     * The number of times the job may be attempted.
     *
     * @var int
     */
    public $tries = 3;

    /**
     * The number of seconds the job can run before timing out.
     *
     * @var int
     */
    public $timeout = 60;

    /**
     * The stem task instance.
     *
     * @var \App\Models\UploadStemTask
     */
    protected $stemTask;

    /**
     * Create a new job instance.
     */
    public function __construct(UploadStemTask $stemTask)
    {
        $this->stemTask = $stemTask;
    }

    /**
     * Execute the job.
     */
    public function handle(AudioAnalysisService $analysisService): void
    {
        // Check if the task is still processing
        if (!$this->stemTask->isProcessing()) {
            Log::info('Stem task no longer processing', [
                'task_id' => $this->stemTask->task_id,
                'status' => $this->stemTask->status
            ]);
            return;
        }

        // Check the current status from the API
        $success = $analysisService->checkStemTaskStatus($this->stemTask);

        if (!$success) {
            Log::warning('Failed to check stem task status', [
                'task_id' => $this->stemTask->task_id
            ]);

            // Retry later if we couldn't check the status
            $this->release(30);
            return;
        }

        // Refresh the model to get updated status
        $this->stemTask->refresh();

        // If still processing, schedule another check
        if ($this->stemTask->isProcessing()) {
            Log::debug('Stem task still processing, scheduling next check', [
                'task_id' => $this->stemTask->task_id,
                'progress' => $this->stemTask->progress
            ]);

            // Schedule next check in 30 seconds
            self::dispatch($this->stemTask)->delay(now()->addSeconds(30));
        } elseif ($this->stemTask->isCompleted()) {
            Log::info('Stem task completed successfully', [
                'task_id' => $this->stemTask->task_id,
                'upload_id' => $this->stemTask->upload_id
            ]);
        } elseif ($this->stemTask->hasFailed()) {
            Log::warning('Stem task failed', [
                'task_id' => $this->stemTask->task_id,
                'error' => $this->stemTask->error_message
            ]);
        }
    }

    /**
     * Handle a job failure.
     */
    public function failed(\Throwable $exception): void
    {
        Log::error('CheckStemTaskStatus job failed', [
            'task_id' => $this->stemTask->task_id,
            'error' => $exception->getMessage()
        ]);

        $this->stemTask->markFailed('Job failed: ' . $exception->getMessage());
    }
}
