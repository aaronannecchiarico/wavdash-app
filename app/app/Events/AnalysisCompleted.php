<?php

namespace App\Events;

use App\Models\Upload;
use App\Models\UploadAnalysisTask;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class AnalysisCompleted implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    /**
     * The upload instance.
     */
    public Upload $upload;

    /**
     * The analysis task instance.
     */
    public UploadAnalysisTask $analysisTask;

    /**
     * Create a new event instance.
     */
    public function __construct(Upload $upload, UploadAnalysisTask $analysisTask)
    {
        $this->upload = $upload;
        $this->analysisTask = $analysisTask;
    }

    /**
     * Get the channels the event should broadcast on.
     *
     * @return array<int, \Illuminate\Broadcasting\Channel>
     */
    public function broadcastOn(): array
    {
        return [
            new PrivateChannel('App.Models.User.'.$this->upload->user_id),
        ];
    }

    /**
     * The event's broadcast name.
     */
    public function broadcastAs(): string
    {
        return 'analysis.completed';
    }

    /**
     * Get the data to broadcast.
     *
     * @return array<string, mixed>
     */
    public function broadcastWith(): array
    {
        return [
            'upload_id' => $this->upload->id,
            'task_id' => $this->analysisTask->task_id,
            'status' => $this->analysisTask->status,
            'has_analysis' => $this->upload->analysis !== null,
            'error_message' => $this->analysisTask->error_message,
            'analysis_url' => route('uploads.analysis.show', $this->upload->id),
        ];
    }
}
