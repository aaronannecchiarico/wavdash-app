<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\UploadStem;
use App\Models\UploadStemTask;
use App\Models\User;
use App\Services\AudioAnalysisService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use Inertia\Testing\AssertableInertia as Assert;
use Tests\TestCase;

class UploadStemControllerTest extends TestCase
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

        // Fake storage to prevent file system operations
        Storage::fake('r2');
        Storage::fake('r2_private');
        Storage::fake('r2_public');
        Storage::fake('private');
        Storage::fake('public');
    }

    public function test_show_requires_authentication(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $response = $this->get(route('uploads.stems.show', $upload));

        $response->assertRedirect(route('login'));
    }

    public function test_show_returns_proper_inertia_response(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $response = $this->actingAs($user)->get(route('uploads.stems.show', $upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/stems')
                ->has('upload.data')
                ->has('analysis_service', fn (Assert $service) => $service
                    ->has('enabled')
                    ->has('available')
                )
            );
    }

    public function test_show_requires_upload_authorization(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user1->id]);

        $response = $this->actingAs($user2)->get(route('uploads.stems.show', $upload));

        $response->assertForbidden();
    }

    public function test_store_requires_authentication(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $response = $this->post(route('uploads.stems.store', $upload));

        $response->assertRedirect(route('login'));
    }

    public function test_store_requires_upload_authorization(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user1->id]);

        $response = $this->actingAs($user2)->post(route('uploads.stems.store', $upload));

        $response->assertForbidden();
    }

    public function test_store_fails_when_service_disabled(): void
    {
        Config::set('services.audio_analysis.enabled', false);

        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id, 'status' => 'ready']);

        $response = $this->actingAs($user)->post(route('uploads.stems.store', $upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Audio analysis service is currently disabled.');
    }

    public function test_store_fails_when_upload_not_ready(): void
    {
        Config::set('services.audio_analysis.enabled', true);

        $user = User::factory()->create();
        $upload = Upload::factory()->make(['user_id' => $user->id, 'status' => 'processing']);
        $upload->save();

        // Verify upload status before making request
        $this->assertEquals('processing', $upload->status);

        $response = $this->actingAs($user)->post(route('uploads.stems.store', $upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Upload must be processed before stem separation can begin.');
    }

    public function test_store_fails_when_stem_separation_already_in_progress(): void
    {
        Config::set('services.audio_analysis.enabled', true);

        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id, 'status' => 'ready']);
        UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'processing',
        ]);

        $this->mock(AudioAnalysisService::class, function ($mock) {
            $mock->shouldReceive('isServiceAvailable')->andReturn(true);
        });

        $response = $this->actingAs($user)->post(route('uploads.stems.store', $upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Stem separation is already in progress for this upload.');
    }

    public function test_store_fails_when_stems_already_exist(): void
    {
        Config::set('services.audio_analysis.enabled', true);

        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id, 'status' => 'ready']);
        UploadStem::factory()->create(['upload_id' => $upload->id]);

        $this->mock(AudioAnalysisService::class, function ($mock) {
            $mock->shouldReceive('isServiceAvailable')->andReturn(true);
        });

        $response = $this->actingAs($user)->post(route('uploads.stems.store', $upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Stem separation already completed for this upload.');
    }

    public function test_store_successfully_starts_stem_separation(): void
    {
        Config::set('services.audio_analysis.enabled', true);

        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id, 'status' => 'ready']);

        $mockTask = UploadStemTask::factory()->make([
            'upload_id' => $upload->id,
            'task_id' => 'test-task-123',
            'status' => 'pending',
        ]);

        $this->mock(AudioAnalysisService::class, function ($mock) use ($mockTask) {
            $mock->shouldReceive('isServiceAvailable')->andReturn(true);
            $mock->shouldReceive('submitForStemSeparation')->andReturn($mockTask);
        });

        $response = $this->actingAs($user)->post(route('uploads.stems.store', $upload));

        $response->assertRedirect()
            ->assertSessionHas('success', 'Stem separation started successfully! You will be notified when it completes.');
    }

    public function test_destroy_requires_authentication(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $response = $this->delete(route('uploads.stems.destroy', $upload));

        $response->assertRedirect(route('login'));
    }

    public function test_destroy_requires_upload_authorization(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user1->id]);

        $response = $this->actingAs($user2)->delete(route('uploads.stems.destroy', $upload));

        $response->assertForbidden();
    }

    public function test_destroy_successfully_deletes_stems_and_task(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $stemTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'completed',
        ]);

        $stem1 = UploadStem::factory()->create(['upload_id' => $upload->id, 'stem_type' => 'vocals']);
        $stem2 = UploadStem::factory()->create(['upload_id' => $upload->id, 'stem_type' => 'drums']);

        $response = $this->actingAs($user)->delete(route('uploads.stems.destroy', $upload));

        $response->assertRedirect()
            ->assertSessionHas('success', 'Stem separation data deleted successfully.');

        $this->assertDatabaseMissing('upload_stems', ['id' => $stem1->id]);
        $this->assertDatabaseMissing('upload_stems', ['id' => $stem2->id]);
        $this->assertDatabaseMissing('upload_stem_tasks', ['id' => $stemTask->id]);
    }

    public function test_destroy_prevents_deletion_when_processing(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $stemTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'processing',
        ]);

        $response = $this->actingAs($user)->delete(route('uploads.stems.destroy', $upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Cannot delete stem separation while it is still processing.');

        $this->assertDatabaseHas('upload_stem_tasks', ['id' => $stemTask->id]);
    }

    public function test_delete_task_requires_authentication(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $response = $this->delete(route('uploads.stems.delete-task', $upload));

        $response->assertRedirect(route('login'));
    }

    public function test_delete_task_requires_upload_authorization(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user1->id]);

        $response = $this->actingAs($user2)->delete(route('uploads.stems.delete-task', $upload));

        $response->assertForbidden();
    }

    public function test_delete_task_successfully_cancels_processing_task(): void
    {
        Config::set('services.audio_analysis.enabled', true);

        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $stemTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'processing',
        ]);

        $this->mock(AudioAnalysisService::class, function ($mock) {
            $mock->shouldReceive('isServiceAvailable')->andReturn(true);
            $mock->shouldReceive('deleteStemTask')->andReturn(true);
        });

        $response = $this->actingAs($user)->delete(route('uploads.stems.delete-task', $upload));

        $response->assertRedirect()
            ->assertSessionHas('success', 'Stem separation task has been cancelled and deleted. You can now start a new separation.');
    }

    public function test_download_stem_requires_authentication(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $response = $this->get(route('uploads.stems.download', ['upload' => $upload, 'stemType' => 'vocals']));

        $response->assertRedirect(route('login'));
    }

    public function test_download_stem_requires_upload_authorization(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user1->id]);

        $response = $this->actingAs($user2)->get(route('uploads.stems.download', ['upload' => $upload, 'stemType' => 'vocals']));

        $response->assertForbidden();
    }

    public function test_download_stem_returns_error_when_stem_not_found(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $response = $this->actingAs($user)->get(route('uploads.stems.download', ['upload' => $upload, 'stemType' => 'vocals']));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Stem not found.');
    }

    public function test_status_returns_json_response(): void
    {
        $user = User::factory()->create();

        $this->mock(AudioAnalysisService::class, function ($mock) {
            $mock->shouldReceive('getServiceStatus')->andReturn([
                'enabled' => true,
                'available' => true,
                'storage_type' => 'r2',
            ]);
        });

        $response = $this->actingAs($user)->get(route('stems.status'));

        $response->assertOk()
            ->assertJson([
                'enabled' => true,
                'available' => true,
                'storage_type' => 'r2',
            ]);
    }
}
