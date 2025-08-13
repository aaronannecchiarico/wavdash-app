<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\UploadAnalysisTask;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
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
        $callbackData = [
            'task_id' => 'test-task-123',
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
        $stemPaths = $this->upload->r2_stems_paths;
        $this->assertNotNull($stemPaths);
        $this->assertArrayHasKey('vocals', $stemPaths);
        $this->assertArrayHasKey('drums', $stemPaths);
        $this->assertArrayHasKey('bass', $stemPaths);
        $this->assertArrayHasKey('other', $stemPaths);
        $this->assertArrayNotHasKey('original', $stemPaths); // Original should be filtered out
    }

    public function test_handles_failed_callback(): void
    {
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
        $response->assertJson(['error' => 'Analysis task not found']);
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
}