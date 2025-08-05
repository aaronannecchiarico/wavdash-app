<?php

namespace App\Jobs;

use App\Models\Upload;
use FFMpeg\Format\Audio\Vorbis;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\App;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use ProtoneMedia\LaravelFFMpeg\Support\FFMpeg;

class ProcessAudioUpload implements ShouldQueue
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
    public $timeout = 300;

    /**
     * The upload instance.
     *
     * @var \App\Models\Upload
     */
    protected $upload;

    /**
     * Create a new job instance.
     */
    public function __construct(Upload $upload)
    {
        $this->upload = $upload;
    }

    /**
     * Execute the job.
     */
    public function handle(): void
    {
        // Update upload status to processing
        $this->upload->update(['status' => 'processing']);

        try {
            $filename = pathinfo($this->upload->filename, PATHINFO_FILENAME);
            $duration = 0;

            $extension = 'ogg';
            $destinationPath = 'uploads/stream/'.Str::slug($filename).'-'.Str::uuid().'.'.$extension;

            $ffmpeg = FFMpeg::fromDisk('private')->open($this->upload->path);

            // Get duration
            $duration = $ffmpeg->getDurationInSeconds();

            // Export to OGG format
            $format = new Vorbis();
            $format->setAudioChannels(2)->setAudioKiloBitrate(128);

            $ffmpeg->export()->toDisk('public')->inFormat($format)->save($destinationPath);

            // Update the upload record with the streamable path and set status to ready
            $this->upload->update([
                'stream_path' => $destinationPath,
                'status' => 'ready',
                'duration' => $duration,
            ]);

            // Broadcast the event
            \App\Events\UploadProcessed::dispatch($this->upload);

            Log::info('Audio file processed successfully', ['upload_id' => $this->upload->id]);
        } catch (\Exception $e) {
            Log::error('Failed to process audio file', [
                'upload_id' => $this->upload->id,
                'error' => $e->getMessage(),
            ]);

            $this->upload->update(['status' => 'failed']);

            // Broadcast the event
            \App\Events\UploadProcessed::dispatch($this->upload);

            throw $e;
        }
    }
}
