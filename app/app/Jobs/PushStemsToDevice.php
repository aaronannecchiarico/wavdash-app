<?php

namespace App\Jobs;

use App\Models\Upload;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class PushStemsToDevice implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    public int $timeout = 120;

    public function __construct(
        public Upload $upload,
    ) {}

    public function handle(): void
    {
        $deviceUrl = config('services.stem_device.url');
        if (empty($deviceUrl)) {
            return;
        }

        $upload = $this->upload->load(['stems', 'analysis']);
        $bpm = $upload->analysis?->bpm;

        // Step 1: Create song on device
        $response = Http::timeout(30)->post("{$deviceUrl}/api/songs", [
            'title' => $upload->title ?? $upload->filename ?? 'Untitled',
            'bpm' => $bpm,
            'duration' => $upload->duration_seconds,
        ]);

        if (! $response->successful()) {
            Log::error('PushStemsToDevice: Failed to create song on device', [
                'upload_id' => $upload->id,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);
            $this->fail(new \RuntimeException("Device returned {$response->status()}"));

            return;
        }

        $songId = $response->json('song_id');

        // Step 2: Upload each stem file
        $pushed = 0;
        $total = 0;

        foreach ($upload->stems as $stem) {
            if (! $stem->converted_to_ogg || empty($stem->public_path)) {
                continue;
            }

            $total++;

            try {
                $filePath = $stem->public_path;

                // Get file contents from storage
                if ($upload->usesR2Storage()) {
                    $fileContents = Storage::disk('r2_public')->get($filePath);
                } else {
                    $fileContents = Storage::disk('public')->get($filePath);
                }

                if ($fileContents === null) {
                    Log::warning('PushStemsToDevice: Stem file not found', [
                        'stem_type' => $stem->stem_type,
                        'path' => $filePath,
                    ]);

                    continue;
                }

                $stemResponse = Http::timeout(60)
                    ->attach('file', $fileContents, "{$stem->stem_type}.ogg")
                    ->post("{$deviceUrl}/api/songs/{$songId}/stems", [
                        'stem_type' => $stem->stem_type,
                    ]);

                if ($stemResponse->successful()) {
                    $pushed++;
                } else {
                    Log::warning('PushStemsToDevice: Failed to push stem', [
                        'stem_type' => $stem->stem_type,
                        'status' => $stemResponse->status(),
                    ]);
                }
            } catch (\Exception $e) {
                Log::warning('PushStemsToDevice: Exception pushing stem', [
                    'stem_type' => $stem->stem_type,
                    'error' => $e->getMessage(),
                ]);
            }
        }

        if ($pushed === 0 && $total > 0) {
            $this->fail(new \RuntimeException("Failed to push any of {$total} stems to device"));

            return;
        }

        Log::info('PushStemsToDevice: Pushed stems to device', [
            'upload_id' => $upload->id,
            'device_song_id' => $songId,
            'pushed' => $pushed,
            'total' => $total,
        ]);
    }
}
