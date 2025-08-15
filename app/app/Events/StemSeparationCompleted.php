<?php

namespace App\Events;

use App\Models\Upload;
use App\Models\UploadStemTask;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class StemSeparationCompleted implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    /**
     * The upload instance.
     */
    public Upload $upload;

    /**
     * The stem task instance.
     */
    public UploadStemTask $stemTask;

    /**
     * Create a new event instance.
     */
    public function __construct(Upload $upload, UploadStemTask $stemTask)
    {
        $this->upload = $upload;
        $this->stemTask = $stemTask;
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
        return 'stem-separation.completed';
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
            'task_id' => $this->stemTask->task_id,
            'status' => $this->stemTask->status,
            'has_stems' => $this->upload->hasStems(),
            'error_message' => $this->stemTask->error_message,
            'stems_url' => route('uploads.stems.show', $this->upload->id),
        ];
    }
}
