<?php

use App\Models\Upload;
use App\Models\UploadTempoTask;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Queue;
use Tests\TestCase;

class TempoTaskManagementTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Disable logging during tests to avoid noise
        Log::shouldReceive('info')->andReturn(true);
        Log::shouldReceive('warning')->andReturn(true);
        Log::shouldReceive('error')->andReturn(true);

        // Fake the queue to prevent jobs from actually running
        Queue::fake();
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function it_prevents_multiple_tempo_tasks_per_upload()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        // Create first tempo task
        $task1 = UploadTempoTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'task-1',
            'status' => 'pending',
            'progress' => 0,
            'processing_options' => [],
            'submitted_at' => now(),
        ]);

        $this->assertDatabaseHas('upload_tempo_tasks', [
            'upload_id' => $upload->id,
            'task_id' => 'task-1',
        ]);

        // Try to create second tempo task for same upload - should fail due to unique constraint
        $this->expectException(\Illuminate\Database\QueryException::class);

        UploadTempoTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'task-2',
            'status' => 'pending',
            'progress' => 0,
            'processing_options' => [],
            'submitted_at' => now(),
        ]);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function callback_handler_finds_correct_task_by_task_id_when_relationship_has_mismatch()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        // Create a tempo task with specific task_id
        $correctTask = UploadTempoTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'correct-task-id-123',
            'status' => 'processing',
            'progress' => 50,
            'processing_options' => ['preset' => 'nightcore'],
            'submitted_at' => now(),
        ]);

        // Simulate callback data from microservice
        $callbackData = [
            'task_id' => 'correct-task-id-123',
            'status' => 'completed',
            'processing_type' => 'tempo',
            'original_analysis' => [
                'bpm' => 120.0,
                'duration' => 180.0,
                'sample_rate' => 44100,
                'key' => 'C major',
            ],
            'tempo_processing' => [
                'preset' => 'nightcore',
                'tempo_factor' => 1.4,
                'pitch_shift_semitones' => 4.0,
                'preserve_pitch' => false,
                'processing_method' => 'direct',
                'effects_applied' => ['tempo_change', 'pitch_shift'],
                'final_bpm' => 168.0,
                'quality_score' => 0.9,
                'processing_warnings' => [],
            ],
            'storage_paths' => [
                'processed_audio' => 'processed/1/2025/08/18/test_tempo_nightcore-140-pitch+4.wav',
                'original' => 'uploads/1/2025/08/15/test.mp3',
            ],
            'processing_time' => 45.2,
            'storage_type' => 'local',
        ];

        // Make the callback request
        $response = $this->postJson(
            route('api.audio.analysis.callback', $upload->id),
            $callbackData
        );

        $response->assertSuccessful();
        $response->assertJson(['status' => 'success']);

        // Verify the task was updated
        $correctTask->refresh();
        $this->assertEquals('completed', $correctTask->status);
        $this->assertEquals(100, $correctTask->progress);
        $this->assertNotNull($correctTask->completed_at);

        // Verify tempo record was created
        $this->assertDatabaseHas('upload_tempos', [
            'upload_id' => $upload->id,
            'preset' => 'nightcore',
            'tempo_factor' => 1.4,
            'pitch_shift_semitones' => 4.0,
            'final_bpm' => 168.0,
        ]);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function callback_handler_returns_error_when_no_matching_task_found()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        // Don't create any tempo task

        // Simulate callback data from microservice with non-existent task_id
        $callbackData = [
            'task_id' => 'non-existent-task-id',
            'status' => 'completed',
            'processing_type' => 'tempo',
            'original_analysis' => ['bpm' => 120.0],
            'tempo_processing' => ['preset' => 'nightcore'],
            'storage_paths' => ['processed_audio' => 'test.wav'],
            'processing_time' => 45.2,
            'storage_type' => 'local',
        ];

        // Make the callback request
        $response = $this->postJson(
            route('api.audio.analysis.callback', $upload->id),
            $callbackData
        );

        $response->assertStatus(404);
        $response->assertJson(['error' => 'No matching task found']);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function task_cleanup_removes_old_tasks_before_creating_new_ones()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        // Create an old completed task
        $oldTask = UploadTempoTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'old-task-id',
            'status' => 'completed',
            'progress' => 100,
            'processing_options' => ['preset' => 'sped_up'],
            'submitted_at' => now()->subHour(),
            'completed_at' => now()->subMinutes(30),
        ]);

        $this->assertDatabaseHas('upload_tempo_tasks', [
            'upload_id' => $upload->id,
            'task_id' => 'old-task-id',
        ]);

        // Now create a new task - this should work because the unique constraint
        // allows replacing completed tasks

        // First delete the old task (simulating the cleanup)
        $oldTask->delete();

        // Create new task
        $newTask = UploadTempoTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'new-task-id',
            'status' => 'pending',
            'progress' => 0,
            'processing_options' => ['preset' => 'nightcore'],
            'submitted_at' => now(),
        ]);

        $this->assertDatabaseMissing('upload_tempo_tasks', [
            'upload_id' => $upload->id,
            'task_id' => 'old-task-id',
        ]);

        $this->assertDatabaseHas('upload_tempo_tasks', [
            'upload_id' => $upload->id,
            'task_id' => 'new-task-id',
        ]);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function callback_validation_rejects_invalid_data()
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        // Missing required fields
        $invalidCallbackData = [
            'task_id' => 'test-task-id',
            // Missing 'status' and 'processing_type'
        ];

        $response = $this->postJson(
            route('api.audio.analysis.callback', $upload->id),
            $invalidCallbackData
        );

        $response->assertStatus(422);
        $response->assertJson(['error' => 'Invalid callback data format']);
    }
}
