<?php

namespace Tests\Feature\Http\Controllers;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Inertia\Testing\AssertableInertia as Assert;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

/**
 * @see \App\Http\Controllers\UploadController
 */
final class UploadControllerTest extends TestCase
{
    use RefreshDatabase;

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
                    ->where('stream_url', 'http://localhost/storage/uploads/stream/1/2025/08/13/test-file.ogg')
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

        $response->assertRedirect(route('uploads.index', $upload))
            ->assertSessionHas('success');

        $this->assertDatabaseHas('uploads', [
            'id' => $upload->id,
            'title' => 'Updated Title',
            'description' => 'Updated Description',
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
}
