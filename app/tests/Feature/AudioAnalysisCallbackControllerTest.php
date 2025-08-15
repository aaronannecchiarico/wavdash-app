<?php

namespace Tests\Feature;

use App\Events\AnalysisCompleted;
use App\Models\Upload;
use App\Models\UploadAnalysisTask;
use App\Models\UploadStemTask;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Event;
use Tests\TestCase;

class AudioAnalysisCallbackControllerTest extends TestCase
{
    use RefreshDatabase;

    private User $user;
    private Upload $upload;
    private UploadAnalysisTask $analysisTask;

    protected function setUp(): void
    {
        parent::setUp();

        $this->user = User::factory()->create();
        $this->upload = Upload::factory()->create([
            'user_id' => $this->user->id,
            'status' => 'ready',
        ]);
        $this->analysisTask = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
        ]);
    }

    public function test_handles_completed_features_callback(): void
    {
        Event::fake();

        $callbackData = [
            'task_id' => 'test-task-123',
            'status' => 'completed',
            'processing_type' => 'features',
            'storage_paths' => [
                'analysis' => 'processed/2024/08/12/uuid_features.json',
                'original' => 'uploads/2024/08/12/uuid-filename.wav'
            ],
            'analysis_summary' => [
                'bpm' => 120.5,
                'key' => 'C major',
                'key_confidence' => 0.82,
                'loudness_db' => -12.3,
                'brightness' => 2000.0,
                'timbral_complexity' => 0.75
            ],
            'processing_time' => 3.45,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $this->upload->id),
            $callbackData
        );

        $response->assertStatus(200);
        $response->assertJson([
            'status' => 'success',
            'message' => 'Callback processed successfully'
        ]);

        // Verify task was updated
        $this->analysisTask->refresh();
        $this->assertEquals('completed', $this->analysisTask->status);
        $this->assertEquals(100, $this->analysisTask->progress);

        // Verify analysis was created
        $this->upload->refresh();

        // Check that AnalysisCompleted event was broadcasted
        Event::assertDispatched(AnalysisCompleted::class, function ($event) {
            return $event->upload->id === $this->upload->id &&
                   $event->analysisTask->id === $this->analysisTask->id;
        });
        $analysis = $this->upload->analysis;
        $this->assertNotNull($analysis);
        $this->assertEquals('C major', $analysis->musical_key);
        $this->assertEquals(121, $analysis->bpm); // rounded
        $this->assertEquals(0.82, $analysis->key_confidence);
        $this->assertEquals(-12.3, $analysis->loudness_db);
        $this->assertEquals(2000.0, $analysis->brightness);
        $this->assertEquals(0.75, $analysis->timbral_complexity);
        $this->assertEquals(3.45, $analysis->analysis_duration);
    }

    public function test_handles_completed_stems_callback(): void
    {
        // Create a stem task for this test instead of analysis task
        $stemTask = UploadStemTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-stem-task-123',
            'status' => 'processing',
        ]);

        $callbackData = [
            'task_id' => 'test-stem-task-123',
            'status' => 'completed',
            'processing_type' => 'stems',
            'storage_paths' => [
                'vocals' => 'stems/2024/08/12/uuid/vocals.wav',
                'drums' => 'stems/2024/08/12/uuid/drums.wav',
                'bass' => 'stems/2024/08/12/uuid/bass.wav',
                'other' => 'stems/2024/08/12/uuid/other.wav',
                'original' => 'uploads/2024/08/12/uuid-song.wav'
            ],
            'processing_time' => 45.67,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $this->upload->id),
            $callbackData
        );

        $response->assertStatus(200);

        // Verify stems were stored
        $this->upload->refresh();
        $stems = $this->upload->stems;
        
        $this->assertCount(4, $stems);
        $stemTypes = $stems->pluck('stem_type')->toArray();
        $this->assertContains('vocals', $stemTypes);
        $this->assertContains('drums', $stemTypes);
        $this->assertContains('bass', $stemTypes);
        $this->assertContains('other', $stemTypes);
        
        // Verify stem task was marked as completed
        $stemTask->refresh();
        $this->assertEquals('completed', $stemTask->status);
    }

    public function test_handles_failed_callback(): void
    {
        Event::fake();

        $callbackData = [
            'task_id' => 'test-task-123',
            'status' => 'failed',
            'processing_type' => 'features',
            'error_message' => 'Invalid audio format',
            'processing_time' => 1.23,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $this->upload->id),
            $callbackData
        );

        $response->assertStatus(200);

        // Verify task was marked as failed
        $this->analysisTask->refresh();
        $this->assertEquals('failed', $this->analysisTask->status);
        $this->assertStringContainsString('Invalid audio format', $this->analysisTask->error_message);

        // Verify no analysis was created
        $this->upload->refresh();

        // Check that AnalysisCompleted event was broadcasted even for failed tasks
        Event::assertDispatched(AnalysisCompleted::class, function ($event) {
            return $event->upload->id === $this->upload->id &&
                   $event->analysisTask->id === $this->analysisTask->id &&
                   $event->analysisTask->status === 'failed';
        });
        $this->assertNull($this->upload->analysis);
    }

    public function test_validates_callback_data(): void
    {
        $invalidData = [
            'task_id' => 'test-task-123',
            'status' => 'invalid-status', // Invalid status
            'processing_type' => 'features',
            'processing_time' => 3.45,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $this->upload->id),
            $invalidData
        );

        $response->assertStatus(422); // Validation error
    }

    public function test_returns_404_when_analysis_task_not_found(): void
    {
        // Create upload without analysis task
        $uploadWithoutTask = Upload::factory()->create([
            'user_id' => $this->user->id,
        ]);

        $callbackData = [
            'task_id' => 'nonexistent-task',
            'status' => 'completed',
            'processing_type' => 'features',
            'processing_time' => 3.45,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $uploadWithoutTask->id),
            $callbackData
        );

        $response->assertStatus(404);
        $response->assertJson(['error' => 'Task not found']);
    }

    public function test_returns_400_on_task_id_mismatch(): void
    {
        $callbackData = [
            'task_id' => 'wrong-task-id', // Doesn't match the task's task_id
            'status' => 'completed',
            'processing_type' => 'features',
            'processing_time' => 3.45,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $this->upload->id),
            $callbackData
        );

        $response->assertStatus(400);
        $response->assertJson(['error' => 'Task ID mismatch']);
    }

    public function test_handles_missing_analysis_data_gracefully(): void
    {
        $callbackData = [
            'task_id' => 'test-task-123',
            'status' => 'completed',
            'processing_type' => 'features',
            // Missing analysis_summary
            'processing_time' => 3.45,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $this->upload->id),
            $callbackData
        );

        $response->assertStatus(200); // Should still succeed

        // Task should be marked as failed due to missing analysis data
        $this->analysisTask->refresh();
        $this->assertEquals('failed', $this->analysisTask->status);
        $this->assertStringContainsString('No musical analysis data received', $this->analysisTask->error_message);
    }

    public function test_handles_null_analysis_summary_with_file(): void
    {
        Event::fake();

        // This simulates the actual callback data from the microservice
        $callbackData = [
            'task_id' => 'test-task-123',
            'status' => 'completed',
            'processing_type' => 'features',
            'storage_paths' => [
                'analysis' => 'processed/2025/08/13/test_features.json',
                'original' => 'uploads/1/2025/08/13/test.mp3'
            ],
            'analysis_summary' => null,
            'error_message' => null,
            'processing_time' => 1.2,
            'storage_type' => 'local'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $this->upload->id),
            $callbackData
        );

        $response->assertStatus(200);
        $response->assertJson([
            'status' => 'success',
            'message' => 'Callback processed successfully'
        ]);

        // Verify task was updated
        $this->analysisTask->refresh();
        $this->assertEquals('completed', $this->analysisTask->status);
        $this->assertEquals(100, $this->analysisTask->progress);

        // Verify minimal analysis was created
        $this->upload->refresh();
        $analysis = $this->upload->analysis;
        $this->assertNotNull($analysis);
        $this->assertEquals(1.2, $analysis->analysis_duration);

        // Check that AnalysisCompleted event was broadcasted
        Event::assertDispatched(AnalysisCompleted::class, function ($event) {
            return $event->upload->id === $this->upload->id &&
                   $event->analysisTask->id === $this->analysisTask->id;
        });
    }

    public function test_completed_analysis_task_can_be_deleted_properly(): void
    {
        Event::fake();
        
        // Simulate a completed analysis task with analysis data
        $this->analysisTask->update([
            'status' => 'completed',
            'progress' => 100,
            'completed_at' => now()
        ]);
        
        $this->upload->analysis()->create([
            'musical_key' => 'C major',
            'bpm' => 120,
            'key_confidence' => 0.85,
            'loudness_db' => -12.5,
            'brightness' => 2500.0,
            'timbral_complexity' => 0.8,
            'analysis_duration' => 3.2,
            'chunk_count' => 5,
            'key_changes' => 1,
        ]);
        
        // Verify initial state
        $this->assertTrue($this->analysisTask->isCompleted());
        $this->assertFalse($this->analysisTask->isProcessing());
        $this->assertNotNull($this->upload->analysis);
        
        // Test the deletion endpoint
        $response = $this->actingAs($this->user)
            ->delete(route('uploads.analysis.destroy', $this->upload));
        
        $response->assertRedirect();
        $response->assertSessionHas('success', 'Analysis data deleted successfully.');
        
        // Verify both analysis and task are deleted
        $this->upload->refresh();
        $this->assertNull($this->upload->analysis);
        $this->assertNull($this->upload->analysisTask);
        
        // Verify database records are actually deleted
        $this->assertDatabaseMissing('upload_analyses', [
            'upload_id' => $this->upload->id
        ]);
        $this->assertDatabaseMissing('upload_analysis_tasks', [
            'id' => $this->analysisTask->id
        ]);
    }
}