<?php

namespace App\Events;

use App\Models\Upload;
use App\Models\UploadTempoTask;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class TempoProcessingCompleted implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    /**
     * The upload instance.
     */
    public Upload $upload;

    /**
     * The tempo task instance.
     */
    public UploadTempoTask $tempoTask;

    /**
     * Create a new event instance.
     */
    public function __construct(Upload $upload, UploadTempoTask $tempoTask)
    {
        $this->upload = $upload;
        $this->tempoTask = $tempoTask;
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
        return 'tempo.completed';
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
            'task_id' => $this->tempoTask->task_id,
            'status' => $this->tempoTask->status,
            'has_tempos' => $this->upload->tempos()->exists(),
            'error_message' => $this->tempoTask->error_message,
            'tempo_url' => route('uploads.tempo.show', $this->upload->id),
            'processing_options' => $this->tempoTask->processing_options,
        ];
    }
}
