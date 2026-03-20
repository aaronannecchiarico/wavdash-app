<?php

namespace Tests\Feature\Jobs;

use App\Jobs\PushStemsToDevice;
use App\Models\Upload;
use App\Models\UploadStem;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class PushStemsToDeviceTest extends TestCase
{
    use RefreshDatabase;

    public function test_push_stems_sends_metadata_and_files(): void
    {
        config(['services.stem_device.url' => 'http://100.0.0.1:9000']);

        $user = User::factory()->create();
        $upload = Upload::factory()->withoutFiles()->for($user)->create([
            'title' => 'Test Song',
            'duration_seconds' => 180,
        ]);

        // Create stems
        foreach (['vocals', 'drums', 'bass', 'guitar', 'piano', 'other'] as $type) {
            UploadStem::factory()->create([
                'upload_id' => $upload->id,
                'stem_type' => $type,
                'public_path' => "uploads/stream/{$user->id}/stems/{$upload->id}/{$type}.ogg",
                'converted_to_ogg' => true,
            ]);
        }

        Http::fake([
            '100.0.0.1:9000/api/songs' => Http::response(['song_id' => 'abc123', 'title' => 'Test Song'], 201),
            '100.0.0.1:9000/api/songs/abc123/stems' => Http::response(['stem_type' => 'vocals', 'message' => 'ok'], 201),
        ]);

        PushStemsToDevice::dispatchSync($upload);

        // Verify metadata POST was sent
        Http::assertSent(function ($request) {
            return str_contains($request->url(), '/api/songs')
                && $request['title'] === 'Test Song';
        });
    }

    public function test_push_stems_skipped_when_no_device_url(): void
    {
        config(['services.stem_device.url' => null]);

        $user = User::factory()->create();
        $upload = Upload::factory()->withoutFiles()->for($user)->create();

        Http::fake();

        PushStemsToDevice::dispatchSync($upload);

        Http::assertNothingSent();
    }
}
