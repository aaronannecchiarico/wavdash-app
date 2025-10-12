<?php

namespace Tests\Feature\Http\Controllers;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use Inertia\Testing\AssertableInertia as Assert;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

/**
 * @see \App\Http\Controllers\UploadController
 */
final class UploadControllerTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Fake HTTP calls to prevent real network requests
        Http::fake([
            '*' => Http::response(['status' => 'healthy'], 200),
        ]);

        // Fake queues to prevent job execution
        Queue::fake();

        // Fake events to prevent real event dispatching
        Event::fake();

        // Fake storage to prevent file system operations
        Storage::fake('r2');
        Storage::fake('r2_private');
        Storage::fake('r2_public');
        Storage::fake('private');
        Storage::fake('public');
    }

    #[Test]
    public function index_requires_authentication()
    {
        $response = $this->get(route('uploads.index'));
        $response->assertRedirect(route('login'));
    }

    #[Test]
    public function index_returns_proper_inertia_response()
    {
        $user = User::factory()->create();

        // Create some uploads for the user - avoid afterCreating hook that copies files
        Upload::factory()->count(3)->for($user)->state(['status' => 'ready'])->create();

        // Create uploads for another user (should not appear)
        $otherUser = User::factory()->create();
        Upload::factory()->count(2)->for($otherUser)->state(['status' => 'ready'])->create();

        $response = $this->actingAs($user)->get(route('uploads.index'));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/index')
                ->has('uploads.data', 3) // Only user's uploads
                ->has('uploads.data.0', fn (Assert $upload) => $upload
                    ->has('id')
                    ->has('title')
                    ->has('filename')
                    ->has('status')
                    ->has('duration')
                    ->has('size')
                    ->has('created_at')
                    ->has('user')
                    ->etc()
                )
                ->has('filters')
                ->has('filterOptions')
                ->has('uploads.links')
                ->has('uploads.meta')
            );
    }

    #[Test]
    public function index_applies_status_filter()
    {
        $user = User::factory()->create();

        // Create uploads with different statuses - disable hooks using make() then save()
        $readyUpload = Upload::factory()->for($user)->make(['status' => 'ready']);
        $readyUpload->save();

        $pendingUpload = Upload::factory()->for($user)->make(['status' => 'pending']);
        $pendingUpload->save();

        $failedUpload = Upload::factory()->for($user)->make(['status' => 'failed']);
        $failedUpload->save();

        // Ensure the uploads were created with correct statuses
        $this->assertEquals('ready', $readyUpload->fresh()->status);
        $this->assertEquals('pending', $pendingUpload->fresh()->status);
        $this->assertEquals('failed', $failedUpload->fresh()->status);

        $response = $this->actingAs($user)->get(route('uploads.index', ['status' => 'pending']));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/index')
                ->has('uploads.data', 1)
                ->where('uploads.data.0.status', 'pending')
                ->where('filters.status', 'pending')
            );
    }

    #[Test]
    public function index_includes_processing_status_filter_options()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get(route('uploads.index'));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/index')
                ->has('filterOptions.processingStatuses.completed')
                ->has('filterOptions.processingStatuses.not_completed')
                ->has('filterOptions.processingStatuses.in_progress')
                ->where('filterOptions.processingStatuses.completed', 'Completed')
                ->where('filterOptions.processingStatuses.not_completed', 'Not Completed')
                ->where('filterOptions.processingStatuses.in_progress', 'In Progress')
            );
    }

    #[Test]
    public function create_returns_proper_inertia_response()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get(route('uploads.create'));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/create')
            );
    }

    #[Test]
    public function show_returns_proper_inertia_response()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->state(['status' => 'ready'])->create();

        $response = $this->actingAs($user)->get(route('uploads.show', $upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/show')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->has('id')
                    ->has('title')
                    ->has('filename')
                    ->has('status')
                    ->has('user')
                    ->etc()
                )
            );
    }

    #[Test]
    public function show_requires_upload_authorization()
    {
        $user = User::factory()->create();
        $otherUser = User::factory()->create();
        $upload = Upload::factory()->for($otherUser)->state(['status' => 'ready'])->create();

        $response = $this->actingAs($user)->get(route('uploads.show', $upload));

        $response->assertForbidden();
    }

    #[Test]
    public function show_includes_stream_url_for_ready_uploads_with_stream_path()
    {
        $user = User::factory()->create();

        // Create upload directly without factory hooks to avoid file operations
        $upload = new \App\Models\Upload([
            'user_id' => $user->id,
            'title' => 'Test Upload',
            'filename' => 'test-file.mp3',
            'path' => 'uploads/1/2025/08/13/test-file.mp3',
            'mime_type' => 'audio/mpeg',
            'size' => 1000000,
            'status' => 'ready',
            'stream_path' => 'uploads/stream/1/2025/08/13/test-file.ogg',
            'uses_r2_storage' => false,
            'r2_upload_path' => null,
        ]);
        $upload->save();

        $response = $this->actingAs($user)->get(route('uploads.show', $upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/show')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->has('stream_url')
                    ->where('stream_url', '/storage/uploads/stream/1/2025/08/13/test-file.ogg')
                    ->etc()
                )
            );
    }

    #[Test]
    public function show_includes_r2_stream_url_for_r2_uploads()
    {
        $user = User::factory()->create();

        // Create upload without factory hooks to avoid file operations
        $upload = Upload::factory()->for($user)->make([
            'status' => 'ready',
            'stream_path' => 'uploads/stream/1/2025/08/13/test-file.ogg',
            'uses_r2_storage' => true,
            'r2_upload_path' => 'uploads/1/2025/08/13/test-file.mp3', // Now stored in private bucket without prefix
        ]);
        $upload->save();

        // Mock R2 public URL configuration for two-bucket system
        config(['filesystems.disks.r2_public.url' => 'https://example.r2.dev']);

        $response = $this->actingAs($user)->get(route('uploads.show', $upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/show')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->has('stream_url')
                    ->where('stream_url', 'https://example.r2.dev/uploads/stream/1/2025/08/13/test-file.ogg')
                    ->etc()
                )
            );
    }

    #[Test]
    public function show_excludes_stream_url_for_non_ready_uploads()
    {
        $user = User::factory()->create();

        // Create upload without factory hooks to avoid file operations
        $upload = Upload::factory()->for($user)->make([
            'status' => 'processing',
            'stream_path' => 'uploads/stream/1/2025/08/13/test-file.ogg',
        ]);
        $upload->save();

        $response = $this->actingAs($user)->get(route('uploads.show', $upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/show')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->missing('stream_url')
                    ->etc()
                )
            );
    }

    #[Test]
    public function show_excludes_stream_url_for_uploads_without_stream_path()
    {
        $user = User::factory()->create();

        // Create upload without factory hooks to avoid file operations
        $upload = Upload::factory()->for($user)->make([
            'status' => 'ready',
            'stream_path' => null,
        ]);
        $upload->save();

        $response = $this->actingAs($user)->get(route('uploads.show', $upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/show')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->missing('stream_url')
                    ->etc()
                )
            );
    }

    #[Test]
    public function edit_returns_proper_inertia_response()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->state(['status' => 'ready'])->create();

        $response = $this->actingAs($user)->get(route('uploads.edit', $upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/edit')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->has('id')
                    ->has('title')
                    ->has('description')
                    ->etc()
                )
            );
    }

    #[Test]
    public function store_validates_required_fields()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->post(route('uploads.store'), [
            'title' => '', // Empty title should fail validation
            'audio_file' => null, // Missing file should fail validation
        ]);

        $response->assertSessionHasErrors(['title', 'audio_file']);
    }

    #[Test]
    public function update_modifies_upload_details()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->state([
            'title' => 'Original Title',
            'description' => 'Original Description',
            'status' => 'ready',
        ])->create();

        $response = $this->actingAs($user)->put(route('uploads.update', $upload), [
            'title' => 'Updated Title',
            'description' => 'Updated Description',
        ]);

        $response->assertRedirect(route('uploads.show', $upload))
            ->assertSessionHas('success');

        $this->assertDatabaseHas('uploads', [
            'id' => $upload->id,
            'title' => 'Updated Title',
            'description' => 'Updated Description',
        ]);
    }

    #[Test]
    public function update_rejects_audio_file_updates_in_phase_4()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->state([
            'title' => 'Original Title',
            'description' => 'Original Description',
            'status' => 'ready',
        ])->create();

        $response = $this->actingAs($user)->put(route('uploads.update', $upload), [
            'title' => 'Updated Title',
            'description' => 'Updated Description',
            'audio_file' => \Illuminate\Http\UploadedFile::fake()->create('new_audio.mp3', 1000, 'audio/mpeg'),
        ]);

        $response->assertRedirect()
            ->assertSessionHasErrors(['audio_file']);

        // Title and description should not be updated when audio_file is provided
        $this->assertDatabaseHas('uploads', [
            'id' => $upload->id,
            'title' => 'Original Title',
            'description' => 'Original Description',
        ]);
    }

    #[Test]
    public function destroy_removes_upload()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->state(['title' => 'Test Upload', 'status' => 'ready'])->create();

        $response = $this->actingAs($user)->delete(route('uploads.destroy', $upload));

        $response->assertRedirect(route('uploads.index'))
            ->assertSessionHas('success');

        $this->assertDatabaseMissing('uploads', [
            'id' => $upload->id,
        ]);
    }

    #[Test]
    public function store_handles_client_processed_upload_when_feature_enabled()
    {
        // Enable client-side processing feature flag
        config(['app.client_side_audio_processing' => true]);

        $user = User::factory()->create();

        // Create a fake OGG file to simulate client-processed audio
        $fakeOggFile = \Illuminate\Http\UploadedFile::fake()->create('processed_audio.ogg', 1000, 'audio/ogg');

        $response = $this->actingAs($user)->post(route('uploads.store'), [
            'title' => 'Client Processed Audio',
            'description' => 'This was processed on the client',
            'audio_file' => $fakeOggFile,
            'client_processed' => true,
            'original_filename' => 'original_audio.mp3',
            'original_size' => 5000000, // 5MB original
            'duration' => 180.5, // 3 minutes 30.5 seconds
        ]);

        $response->assertRedirect(route('uploads.index'))
            ->assertSessionHas('success', 'Audio file uploaded and processed successfully!');

        // Ensure UploadProcessed event was dispatched for client-processed uploads
        Event::assertDispatched(\App\Events\UploadProcessed::class);

        $this->assertDatabaseHas('uploads', [
            'title' => 'Client Processed Audio',
            'description' => 'This was processed on the client',
            'filename' => 'original_audio.mp3',
            'mime_type' => 'audio/ogg',
            'size' => 5000000,
            'status' => 'ready', // Should be immediately ready
            'duration_seconds' => 180.5,
            'user_id' => $user->id,
        ]);
    }

    #[Test]
    public function store_rejects_uploads_without_client_processing()
    {
        $user = User::factory()->create();

        $fakeMp3File = \Illuminate\Http\UploadedFile::fake()->create('audio.mp3', 1000, 'audio/mpeg');

        $response = $this->actingAs($user)->post(route('uploads.store'), [
            'title' => 'Should Be Rejected',
            'description' => 'Server-side processing no longer supported',
            'audio_file' => $fakeMp3File,
            'client_processed' => false, // No client processing
        ]);

        $response->assertRedirect()
            ->assertSessionHasErrors(['audio_file']);

        // Should not create any upload record
        $this->assertDatabaseMissing('uploads', [
            'title' => 'Should Be Rejected',
        ]);
    }

    #[Test]
    public function store_validates_client_processed_upload_fields()
    {
        config(['app.client_side_audio_processing' => true]);

        $user = User::factory()->create();

        // Missing required client processing fields
        $response = $this->actingAs($user)->post(route('uploads.store'), [
            'title' => 'Invalid Client Upload',
            'audio_file' => \Illuminate\Http\UploadedFile::fake()->create('audio.ogg', 1000, 'audio/ogg'),
            'client_processed' => true,
            // Missing: original_filename, original_size, duration
        ]);

        $response->assertSessionHasErrors(['original_filename', 'original_size', 'duration']);
    }

    #[Test]
    public function store_validates_ogg_mime_type_for_client_processed_files()
    {
        config(['app.client_side_audio_processing' => true]);

        $user = User::factory()->create();

        // Wrong mime type for client-processed file (should be OGG)
        $response = $this->actingAs($user)->post(route('uploads.store'), [
            'title' => 'Wrong Format',
            'audio_file' => \Illuminate\Http\UploadedFile::fake()->create('audio.mp3', 1000, 'audio/mpeg'),
            'client_processed' => true,
            'original_filename' => 'original.mp3',
            'original_size' => 1000,
            'duration' => 60,
        ]);

        $response->assertSessionHasErrors(['audio_file']);
    }

    #[Test]
    public function store_rejects_non_client_processed_files_in_phase_4()
    {
        $user = User::factory()->create();

        // Server-processed file with MP3 format should now be rejected
        $response = $this->actingAs($user)->post(route('uploads.store'), [
            'title' => 'Server Processed MP3',
            'audio_file' => \Illuminate\Http\UploadedFile::fake()->create('audio.mp3', 1000, 'audio/mpeg'),
            'client_processed' => false, // Explicitly server processing
        ]);

        $response->assertRedirect()
            ->assertSessionHasErrors(['audio_file']);

        $this->assertDatabaseMissing('uploads', [
            'title' => 'Server Processed MP3',
        ]);
    }

    #[Test]
    public function store_creates_proper_file_paths_for_client_processed_uploads()
    {
        config(['app.client_side_audio_processing' => true]);

        $user = User::factory()->create();

        $fakeOggFile = \Illuminate\Http\UploadedFile::fake()->create('processed_audio.ogg', 1000, 'audio/ogg');

        $response = $this->actingAs($user)->post(route('uploads.store'), [
            'title' => 'Path Test Audio',
            'audio_file' => $fakeOggFile,
            'client_processed' => true,
            'original_filename' => 'original_audio.mp3',
            'original_size' => 5000000,
            'duration' => 180.5,
        ]);

        $response->assertRedirect(route('uploads.index'));

        // Ensure event was fired for processed upload
        Event::assertDispatched(\App\Events\UploadProcessed::class);

        $upload = Upload::where('title', 'Path Test Audio')->first();

        $this->assertNotNull($upload);
        $this->assertStringContainsString('path-test-audio', $upload->stream_path);
        $this->assertStringEndsWith('.ogg', $upload->stream_path);
        $this->assertEquals($upload->path, $upload->stream_path); // Should be same for processed files
    }
}