<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\UploadAnalysis;
use App\Models\UploadAnalysisTask;
use App\Models\User;
use App\Services\AudioAnalysisService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class AudioAnalysisTest extends TestCase
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

    public function test_upload_can_have_analysis_task(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create([
            'user_id' => $user->id,
        ]);

        $analysisTask = UploadAnalysisTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'test-task-123',
            'status' => 'pending',
            'progress' => 0,
            'submitted_at' => now(),
        ]);

        $this->assertInstanceOf(UploadAnalysisTask::class, $upload->analysisTask);
        $this->assertEquals('test-task-123', $upload->analysisTask->task_id);
        $this->assertTrue($upload->analysisTask->isProcessing());
        $this->assertFalse($upload->analysisTask->isCompleted());
    }

    public function test_upload_can_have_analysis_results(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create([
            'user_id' => $user->id,
        ]);

        $analysis = UploadAnalysis::create([
            'upload_id' => $upload->id,
            'musical_key' => 'E major',
            'key_confidence' => 0.85,
            'bpm' => 120,
            'beat_regularity' => 0.78,
            'loudness_db' => -12.3,
            'dynamic_range_db' => 18.2,
            'brightness' => 1850.2,
            'timbral_complexity' => 0.45,
        ]);

        $this->assertInstanceOf(UploadAnalysis::class, $upload->analysis);
        $this->assertEquals('E major', $upload->analysis->musical_key);
        $this->assertEquals(120, $upload->analysis->bpm);
        $this->assertTrue($upload->hasAnalysis());
    }

    public function test_analysis_task_status_methods(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create([
            'user_id' => $user->id,
        ]);

        $task = UploadAnalysisTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'test-task-456',
            'status' => 'processing',
            'progress' => 50,
            'submitted_at' => now(),
        ]);

        $this->assertTrue($task->isProcessing());
        $this->assertFalse($task->isCompleted());
        $this->assertFalse($task->hasFailed());

        $task->markCompleted();
        $this->assertTrue($task->isCompleted());
        $this->assertFalse($task->isProcessing());
        $this->assertEquals(100, $task->progress);

        $task2 = UploadAnalysisTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'test-task-789',
            'status' => 'pending',
        ]);

        $task2->markFailed('Test error message');
        $this->assertTrue($task2->hasFailed());
        $this->assertFalse($task2->isProcessing());
        $this->assertEquals('Test error message', $task2->error_message);
    }

    public function test_analysis_category_methods(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create([
            'user_id' => $user->id,
        ]);

        $analysis = UploadAnalysis::create([
            'upload_id' => $upload->id,
            'musical_key' => 'C major',
            'key_confidence' => 0.9,
            'bpm' => 128,
            'loudness_db' => -10.0,
            'dynamic_range_db' => 15.0,
            'brightness' => 1500.0,
        ]);

        $this->assertEquals('Upbeat', $analysis->getBpmCategory());
        $this->assertEquals('Loud', $analysis->getLoudnessCategory());
        $this->assertEquals('Moderate', $analysis->getDynamicRangeCategory());
        $this->assertEquals('Balanced', $analysis->getBrightnessCategory());
        $this->assertTrue($analysis->hasReliableKey());
        $this->assertFalse($analysis->isAtonalComplex());
    }

    public function test_audio_analysis_service_availability_check(): void
    {
        // Mock the Http facade to prevent actual HTTP calls
        \Illuminate\Support\Facades\Http::fake([
            '*' => \Illuminate\Support\Facades\Http::response(['status' => 'healthy'], 200),
        ]);

        $service = $this->app->make(AudioAnalysisService::class);

        // This will now use the mocked response
        $isAvailable = $service->isServiceAvailable();
        $this->assertIsBool($isAvailable);
        $this->assertTrue($isAvailable);
    }

    public function test_similar_uploads_finding(): void
    {
        $user = User::factory()->create();

        $baseUpload = Upload::factory()->create(['user_id' => $user->id]);
        UploadAnalysis::create([
            'upload_id' => $baseUpload->id,
            'musical_key' => 'C major',
            'key_confidence' => 0.85,
            'bpm' => 120,
            'brightness' => 1500.0,
        ]);

        $similarUpload1 = Upload::factory()->create(['user_id' => $user->id]);
        UploadAnalysis::create([
            'upload_id' => $similarUpload1->id,
            'musical_key' => 'C major',
            'key_confidence' => 0.9,
            'bpm' => 125, // Within ±10 BPM
            'brightness' => 1400.0, // Within ±20%
        ]);

        $similarUpload2 = Upload::factory()->create(['user_id' => $user->id]);
        UploadAnalysis::create([
            'upload_id' => $similarUpload2->id,
            'musical_key' => 'C major',
            'key_confidence' => 0.8,
            'bpm' => 115, // Within ±10 BPM
            'brightness' => 1600.0, // Within ±20%
        ]);

        $dissimilarUpload = Upload::factory()->create(['user_id' => $user->id]);
        UploadAnalysis::create([
            'upload_id' => $dissimilarUpload->id,
            'musical_key' => 'F# minor',
            'key_confidence' => 0.7,
            'bpm' => 80, // Outside ±10 BPM range
            'brightness' => 2500.0, // Outside ±20% range
        ]);

        $service = $this->app->make(AudioAnalysisService::class);
        $similar = $service->findSimilarUploads($baseUpload, 10);

        // Should find the 2 similar uploads but not the dissimilar one
        $this->assertEquals(2, $similar->count());
        $this->assertTrue($similar->contains('id', $similarUpload1->id));
        $this->assertTrue($similar->contains('id', $similarUpload2->id));
        $this->assertFalse($similar->contains('id', $dissimilarUpload->id));
    }
}
