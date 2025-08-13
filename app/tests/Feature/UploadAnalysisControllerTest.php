<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\UploadAnalysis;
use App\Models\UploadAnalysisTask;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Inertia\Testing\AssertableInertia as Assert;
use Tests\TestCase;

class UploadAnalysisControllerTest extends TestCase
{
    use RefreshDatabase;

    protected User $user;
    protected Upload $upload;

    protected function setUp(): void
    {
        parent::setUp();

        $this->user = User::factory()->create();
        $this->upload = Upload::factory()->create([
            'user_id' => $this->user->id,
            'status' => 'ready'
        ]);
    }

    public function test_analysis_service_status_endpoint(): void
    {
        $response = $this->actingAs($this->user)
            ->getJson(route('analysis.status'));

        $response->assertOk()
            ->assertJsonStructure([
                'enabled',
                'available',
                'base_url'
            ]);
    }

    public function test_can_view_analysis_page_for_upload(): void
    {
        $response = $this->actingAs($this->user)
            ->get(route('uploads.analysis.show', $this->upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/analysis')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->where('id', $this->upload->id)
                    ->has('id')
                    ->has('title')
                    ->has('status')
                    ->etc()
                )
                ->has('analysis_service', fn (Assert $service) => $service
                    ->has('enabled')
                    ->has('available')
                )
            );
    }

    public function test_cannot_start_analysis_when_service_disabled(): void
    {
        config(['services.audio_analysis.enabled' => false]);

        $response = $this->actingAs($this->user)
            ->post(route('uploads.analysis.store', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Audio analysis is currently disabled.');
    }

    public function test_cannot_start_analysis_when_upload_not_ready(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        $this->upload->update(['status' => 'processing']);

        $response = $this->actingAs($this->user)
            ->post(route('uploads.analysis.store', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Upload must be processed before analysis can begin.');
    }

    public function test_cannot_start_analysis_when_already_in_progress(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        // Create an existing analysis task in progress
        UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'progress' => 50,
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->post(route('uploads.analysis.store', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Analysis is already in progress for this upload.');
    }

    public function test_cannot_start_analysis_when_already_completed(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        // Create completed analysis
        UploadAnalysis::create([
            'upload_id' => $this->upload->id,
            'musical_key' => 'C major',
            'bpm' => 120,
        ]);

        $response = $this->actingAs($this->user)
            ->post(route('uploads.analysis.store', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Analysis already completed for this upload.');
    }

    public function test_can_delete_completed_analysis(): void
    {
        // Create completed analysis
        $analysis = UploadAnalysis::create([
            'upload_id' => $this->upload->id,
            'musical_key' => 'C major',
            'bpm' => 120,
        ]);

        $analysisTask = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'completed',
            'progress' => 100,
            'submitted_at' => now(),
            'completed_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.destroy', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('success', 'Analysis data deleted successfully.');

        $this->assertDatabaseMissing('upload_analyses', ['id' => $analysis->id]);
        $this->assertDatabaseMissing('upload_analysis_tasks', ['id' => $analysisTask->id]);
    }

    public function test_cannot_delete_analysis_while_processing(): void
    {
        UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'progress' => 50,
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.destroy', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Cannot delete analysis while it is still processing.');
    }

    public function test_can_view_similar_uploads_page(): void
    {
        // Create analysis data for the upload
        UploadAnalysis::create([
            'upload_id' => $this->upload->id,
            'musical_key' => 'E major',
            'key_confidence' => 0.85,
            'bpm' => 128,
            'loudness_db' => -12.0,
            'brightness' => 1800,
        ]);

        // Create similar uploads for comparison
        $similarUpload = Upload::factory()->create([
            'user_id' => $this->user->id,
            'status' => 'ready'
        ]);

        UploadAnalysis::create([
            'upload_id' => $similarUpload->id,
            'musical_key' => 'E major',
            'bpm' => 126,
            'brightness' => 1750,
        ]);

        $response = $this->actingAs($this->user)
            ->get(route('uploads.analysis.similar', $this->upload));

        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/similar')
                ->has('upload.data', fn (Assert $upload) => $upload
                    ->where('id', $this->upload->id)
                    ->etc()
                )
                ->has('similar_uploads')
                ->has('analysis_criteria', fn (Assert $criteria) => $criteria
                    ->where('musical_key', 'E major')
                    ->where('bpm', 128)
                    ->where('brightness', 1800)
                    ->where('key_confidence', 0.85)
                )
            );
    }

    public function test_cannot_view_similar_uploads_without_analysis(): void
    {
        $response = $this->actingAs($this->user)
            ->get(route('uploads.analysis.similar', $this->upload));

        $response->assertRedirect(route('uploads.analysis.show', $this->upload))
            ->assertSessionHas('error', 'Upload has no analysis data to compare against.');
    }

    public function test_unauthorized_user_cannot_access_others_analysis(): void
    {
        $otherUser = User::factory()->create();
        $otherUpload = Upload::factory()->create(['user_id' => $otherUser->id]);

        $response = $this->actingAs($this->user)
            ->get(route('uploads.analysis.show', $otherUpload));

        $response->assertForbidden();
    }

    public function test_analysis_data_included_in_upload_resource(): void
    {
        // Create analysis data
        $analysisTask = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'completed',
            'progress' => 100,
            'submitted_at' => now(),
            'completed_at' => now(),
        ]);

        $analysis = UploadAnalysis::create([
            'upload_id' => $this->upload->id,
            'musical_key' => 'E major',
            'key_confidence' => 0.85,
            'bpm' => 128,
            'loudness_db' => -12.0,
            'brightness' => 1800.0,
        ]);

        $response = $this->actingAs($this->user)
            ->get(route('uploads.show', $this->upload));

        // The response should be an Inertia response with upload data including analysis
        $response->assertOk();

        // Check that the upload resource includes analysis data when loaded
        $this->upload->load(['analysisTask', 'analysis']);
        $this->assertNotNull($this->upload->analysisTask);
        $this->assertNotNull($this->upload->analysis);
        $this->assertEquals('E major', $this->upload->analysis->musical_key);
        $this->assertEquals(128, $this->upload->analysis->bpm);
    }

    public function test_can_delete_processing_analysis_task(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        Http::fake([
            '*/health' => Http::response(['status' => 'healthy']),
            '*/task/test-task-123' => Http::response([
                'task_id' => 'test-task-123',
                'status' => 'deleted',
                'message' => 'Task deleted successfully'
            ])
        ]);

        $task = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'progress' => 50,
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('success', 'Analysis task has been cancelled and deleted. You can now start a new analysis.');

        $task->refresh();
        $this->assertEquals('deleted', $task->status);
        $this->assertEquals('Task deleted by user', $task->error_message);
    }

    public function test_can_delete_pending_analysis_task(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        $task = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'pending',
            'progress' => 0,
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('success', 'Analysis task has been cancelled and deleted. You can now start a new analysis.');

        $task->refresh();
        $this->assertEquals('deleted', $task->status);
    }

    public function test_can_delete_failed_analysis_task(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        $task = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'failed',
            'error_message' => 'Original error',
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('success', 'Analysis task has been cancelled and deleted. You can now start a new analysis.');

        $task->refresh();
        $this->assertEquals('deleted', $task->status);
    }

    public function test_cannot_delete_completed_analysis_task(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        $task = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'completed',
            'progress' => 100,
            'submitted_at' => now(),
            'completed_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'This analysis task cannot be deleted in its current state.');

        $task->refresh();
        $this->assertEquals('completed', $task->status); // Should remain unchanged
    }

    public function test_cannot_delete_task_when_no_task_exists(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'No analysis task found to delete.');
    }

    public function test_cannot_delete_task_when_service_disabled(): void
    {
        config(['services.audio_analysis.enabled' => false]);

        $task = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('error', 'Audio analysis is currently disabled.');
    }

    public function test_delete_task_removes_existing_analysis_data(): void
    {
        config(['services.audio_analysis.enabled' => true]);

        // Create completed analysis first
        $analysis = UploadAnalysis::create([
            'upload_id' => $this->upload->id,
            'musical_key' => 'C major',
            'bpm' => 120,
        ]);

        $task = UploadAnalysisTask::create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $this->upload));

        $response->assertRedirect()
            ->assertSessionHas('success');

        // Verify analysis data was removed
        $this->assertDatabaseMissing('upload_analyses', ['id' => $analysis->id]);

        $task->refresh();
        $this->assertEquals('deleted', $task->status);
    }

    public function test_unauthorized_user_cannot_delete_analysis_task(): void
    {
        $otherUser = User::factory()->create();
        $otherUpload = Upload::factory()->create(['user_id' => $otherUser->id]);

        UploadAnalysisTask::create([
            'upload_id' => $otherUpload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'submitted_at' => now(),
        ]);

        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.delete-task', $otherUpload));

        $response->assertForbidden();
    }
}