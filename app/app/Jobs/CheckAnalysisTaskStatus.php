<?php

namespace App\Jobs;

use App\Models\UploadAnalysisTask;
use App\Services\AudioAnalysisService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class CheckAnalysisTaskStatus implements ShouldQueue
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
     * The analysis task instance.
     *
     * @var \App\Models\UploadAnalysisTask
     */
    protected $analysisTask;

    /**
     * Create a new job instance.
     */
    public function __construct(UploadAnalysisTask $analysisTask)
    {
        $this->analysisTask = $analysisTask;
    }

    /**
     * Execute the job.
     */
    public function handle(AudioAnalysisService $analysisService): void
    {
        // Check if the task is still processing
        if (! $this->analysisTask->isProcessing()) {
            Log::info('Analysis task no longer processing', [
                'task_id' => $this->analysisTask->task_id,
                'status' => $this->analysisTask->status,
            ]);

            return;
        }

        // Check the current status from the API
        $success = $analysisService->checkTaskStatus($this->analysisTask);

        if (! $success) {
            Log::warning('Failed to check analysis task status', [
                'task_id' => $this->analysisTask->task_id,
            ]);

            // Retry later if we couldn't check the status
            $this->release(30);

            return;
        }

        // Refresh the model to get updated status
        $this->analysisTask->refresh();

        // If still processing, schedule another check
        if ($this->analysisTask->isProcessing()) {
            Log::debug('Analysis task still processing, scheduling next check', [
                'task_id' => $this->analysisTask->task_id,
                'progress' => $this->analysisTask->progress,
            ]);

            // Schedule next check in 30 seconds
            self::dispatch($this->analysisTask)->delay(now()->addSeconds(30));
        } elseif ($this->analysisTask->isCompleted()) {
            Log::info('Analysis task completed successfully', [
                'task_id' => $this->analysisTask->task_id,
                'upload_id' => $this->analysisTask->upload_id,
            ]);
        } elseif ($this->analysisTask->hasFailed()) {
            Log::warning('Analysis task failed', [
                'task_id' => $this->analysisTask->task_id,
                'error' => $this->analysisTask->error_message,
            ]);
        }
    }

    /**
     * Handle a job failure.
     */
    public function failed(\Throwable $exception): void
    {
        Log::error('CheckAnalysisTaskStatus job failed', [
            'task_id' => $this->analysisTask->task_id,
            'error' => $exception->getMessage(),
        ]);

        $this->analysisTask->markFailed('Job failed: '.$exception->getMessage());
    }
}
