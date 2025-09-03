<?php

namespace Tests\Unit;

use App\Models\Upload;
use App\Models\UploadStemTask;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class UploadStemTaskTest extends TestCase
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

    public function test_it_can_be_created_with_required_fields(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $stemTask = UploadStemTask::create([
            'upload_id' => $upload->id,
            'task_id' => 'test-task-123',
            'status' => 'pending',
            'progress' => 0,
            'submitted_at' => now(),
        ]);

        $this->assertInstanceOf(UploadStemTask::class, $stemTask);
        $this->assertEquals($upload->id, $stemTask->upload_id);
        $this->assertEquals('test-task-123', $stemTask->task_id);
        $this->assertEquals('pending', $stemTask->status);
        $this->assertEquals(0, $stemTask->progress);
    }

    public function test_it_belongs_to_an_upload(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);
        $stemTask = UploadStemTask::factory()->create(['upload_id' => $upload->id]);

        $this->assertInstanceOf(Upload::class, $stemTask->upload);
        $this->assertEquals($upload->id, $stemTask->upload->id);
    }

    public function test_it_can_be_marked_as_completed(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);
        $stemTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'processing',
            'progress' => 50,
        ]);

        $stemTask->markCompleted();

        $this->assertEquals('completed', $stemTask->status);
        $this->assertEquals(100, $stemTask->progress);
        $this->assertNotNull($stemTask->completed_at);
    }

    public function test_it_can_be_marked_as_failed(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);
        $stemTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'processing',
        ]);

        $errorMessage = 'Processing failed due to timeout';
        $stemTask->markFailed($errorMessage);

        $this->assertEquals('failed', $stemTask->status);
        $this->assertEquals($errorMessage, $stemTask->error_message);
        $this->assertNotNull($stemTask->completed_at);
    }

    public function test_it_can_check_if_completed(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $completedTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'completed',
        ]);

        $pendingTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'pending',
        ]);

        $this->assertTrue($completedTask->isCompleted());
        $this->assertFalse($pendingTask->isCompleted());
    }

    public function test_it_can_check_if_failed(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $failedTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'failed',
        ]);

        $pendingTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'pending',
        ]);

        $this->assertTrue($failedTask->hasFailed());
        $this->assertFalse($pendingTask->hasFailed());
    }

    public function test_it_can_check_if_processing(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $processingTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'processing',
        ]);

        $pendingTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'pending',
        ]);

        $completedTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'completed',
        ]);

        $this->assertTrue($processingTask->isProcessing());
        $this->assertTrue($pendingTask->isProcessing());
        $this->assertFalse($completedTask->isProcessing());
    }

    public function test_it_can_check_if_deleted(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $deletedTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'deleted',
        ]);

        $pendingTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'pending',
        ]);

        $this->assertTrue($deletedTask->isDeleted());
        $this->assertFalse($pendingTask->isDeleted());
    }

    public function test_it_can_check_if_can_be_deleted(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $pendingTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'pending',
        ]);

        $processingTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'processing',
        ]);

        $failedTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'failed',
        ]);

        $completedTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'status' => 'completed',
        ]);

        $this->assertTrue($pendingTask->canBeDeleted());
        $this->assertTrue($processingTask->canBeDeleted());
        $this->assertTrue($failedTask->canBeDeleted());
        $this->assertFalse($completedTask->canBeDeleted());
    }

    public function test_it_casts_attributes_correctly(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);
        $stemTask = UploadStemTask::factory()->create([
            'upload_id' => $upload->id,
            'progress' => '75',
            'submitted_at' => '2023-01-01 12:00:00',
        ]);

        $this->assertIsInt($stemTask->id);
        $this->assertIsInt($stemTask->upload_id);
        $this->assertIsInt($stemTask->progress);
        $this->assertInstanceOf(\Carbon\Carbon::class, $stemTask->submitted_at);
    }
}
