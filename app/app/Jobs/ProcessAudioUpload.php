<?php

namespace App\Jobs;

use App\Models\Upload;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

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
            // In a production environment, we'd use FFmpeg to transcode the file
            // For local development without FFmpeg, we'll simulate processing by
            // creating a copy of the file and setting it as the streamable version
            
            // Get the source file path
            $sourcePath = $this->upload->path;
            
            // Create the destination path for the processed file
            $filename = pathinfo($this->upload->filename, PATHINFO_FILENAME);
            $extension = pathinfo($this->upload->filename, PATHINFO_EXTENSION);
            
            // For now, we'll use the same extension, but in production we'd convert to OGG
            $destinationPath = 'uploads/stream/' . Str::slug($filename) . '-' . Str::uuid() . '.' . $extension;
            
            // In production, we'd use FFmpeg like this:
            // $ffmpeg = FFMpeg\FFMpeg::create();
            // $audio = $ffmpeg->open(Storage::disk('private')->path($sourcePath));
            // $format = new FFMpeg\Format\Audio\Ogg();
            // $format->setAudioChannels(2)->setAudioKiloBitrate(128);
            // $audio->save($format, Storage::disk('public')->path($destinationPath));
            
            // For local development, we'll simply copy the file
            $sourceContents = Storage::disk('private')->get($sourcePath);
            Storage::disk('public')->put($destinationPath, $sourceContents);
            
            // Update the upload record with the streamable path and set status to ready
            $this->upload->update([
                'stream_path' => $destinationPath,
                'status' => 'ready',
            ]);
            
            Log::info('Audio file processed successfully', ['upload_id' => $this->upload->id]);
        } catch (\Exception $e) {
            Log::error('Failed to process audio file', [
                'upload_id' => $this->upload->id,
                'error' => $e->getMessage(),
            ]);
            
            $this->upload->update(['status' => 'failed']);
            
            throw $e;
        }
    }
}
