<?php

namespace Tests\Unit;

use App\Models\Upload;
use App\Models\UploadAnalysisTask;
use App\Models\User;
use App\Services\AudioAnalysisService;
use App\Services\AudioMicroserviceClient;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AudioAnalysisServiceTest extends TestCase
{
    use RefreshDatabase;

    private AudioAnalysisService $analysisService;

    private AudioMicroserviceClient $mockClient;

    private Upload $upload;

    protected function setUp(): void
    {
        parent::setUp();

        $this->mockClient = $this->createMock(AudioMicroserviceClient::class);
        $this->analysisService = new AudioAnalysisService($this->mockClient);

        $user = User::factory()->create();
        $this->upload = Upload::factory()->create([
            'user_id' => $user->id,
            'uses_r2_storage' => false,
            'path' => 'uploads/original/test.mp3',
        ]);
    }

    public function test_submit_for_analysis_creates_task(): void
    {
        $this->mockClient->expects($this->once())
            ->method('extractFeatures')
            ->with(
                $this->upload->getFilePath(),
                $this->callback(function ($options) {
                    return $options['detailed'] === false &&
                           str_contains($options['callback_url'], 'api/audio/analysis/callback') &&
                           $options['metadata']['upload_id'] === (string) $this->upload->id &&
                           $options['metadata']['user_id'] === (string) $this->upload->user_id;
                })
            )
            ->willReturn([
                'task_id' => 'test-task-123',
                'status' => 'processing',
            ]);

        $task = $this->analysisService->submitForAnalysis($this->upload);

        $this->assertNotNull($task);
        $this->assertEquals('test-task-123', $task->task_id);
        $this->assertEquals('processing', $task->status);
        $this->assertEquals($this->upload->id, $task->upload_id);
    }

    public function test_submit_for_analysis_handles_no_task_id(): void
    {
        $this->mockClient->expects($this->once())
            ->method('extractFeatures')
            ->willReturn(['status' => 'processing']); // No task_id

        $task = $this->analysisService->submitForAnalysis($this->upload);

        $this->assertNull($task);
    }

    public function test_submit_for_analysis_handles_exception(): void
    {
        $this->mockClient->expects($this->once())
            ->method('extractFeatures')
            ->willThrowException(new \Exception('Microservice error'));

        $task = $this->analysisService->submitForAnalysis($this->upload);

        $this->assertNull($task);
    }

    public function test_check_task_status_updates_task(): void
    {
        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'progress' => 50,
        ]);

        $this->mockClient->expects($this->once())
            ->method('getTaskStatus')
            ->with('test-task-123')
            ->willReturn([
                'status' => 'processing',
                'progress' => 75,
            ]);

        $result = $this->analysisService->checkTaskStatus($task);

        $this->assertTrue($result);
        $task->refresh();
        $this->assertEquals('processing', $task->status);
        $this->assertEquals(75, $task->progress);
    }

    public function test_check_task_status_handles_completed(): void
    {
        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
        ]);

        $this->mockClient->expects($this->once())
            ->method('getTaskStatus')
            ->willReturn([
                'status' => 'completed',
                'progress' => 100,
            ]);

        $this->mockClient->expects($this->once())
            ->method('getTaskSummary')
            ->with('test-task-123')
            ->willReturn([
                'analysis_summary' => [
                    'bpm' => 120.5,
                    'key' => 'C major',
                    'key_confidence' => 0.85,
                    'loudness_db' => -12.3,
                    'brightness' => 2000.0,
                ],
                'processing_time' => 3.45,
            ]);

        $result = $this->analysisService->checkTaskStatus($task);

        $this->assertTrue($result);
        $task->refresh();
        $this->assertEquals('completed', $task->status);

        // Check that analysis was created
        $this->upload->refresh();
        $analysis = $this->upload->analysis;
        $this->assertNotNull($analysis);
        $this->assertEquals('C major', $analysis->musical_key);
        $this->assertEquals(121, $analysis->bpm); // rounded
        $this->assertEquals(0.85, $analysis->key_confidence);
    }

    public function test_check_task_status_handles_failed(): void
    {
        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
        ]);

        $this->mockClient->expects($this->once())
            ->method('getTaskStatus')
            ->willReturn([
                'status' => 'failed',
                'error' => 'Processing failed due to invalid file format',
            ]);

        $result = $this->analysisService->checkTaskStatus($task);

        $this->assertTrue($result);
        $task->refresh();
        $this->assertEquals('failed', $task->status);
        $this->assertStringContainsString('Processing failed', $task->error_message);
    }

    public function test_is_service_available(): void
    {
        $this->mockClient->expects($this->once())
            ->method('isServiceAvailable')
            ->willReturn(true);

        $this->assertTrue($this->analysisService->isServiceAvailable());
    }

    public function test_get_service_status_with_storage_info(): void
    {
        $this->mockClient->expects($this->once())
            ->method('isServiceAvailable')
            ->willReturn(true);

        $this->mockClient->expects($this->once())
            ->method('getStorageStatus')
            ->willReturn([
                'storage_type' => 'local',
                'available' => true,
                'total_files' => 42,
            ]);

        $status = $this->analysisService->getServiceStatus();

        $this->assertTrue($status['available']);
        $this->assertEquals('local', $status['storage_type']);
        $this->assertTrue($status['storage_available']);
        $this->assertEquals(42, $status['storage_info']['total_files']);
    }

    public function test_get_service_status_handles_storage_error(): void
    {
        $this->mockClient->expects($this->once())
            ->method('getStorageStatus')
            ->willThrowException(new \Exception('Storage unavailable'));

        $status = $this->analysisService->getServiceStatus();

        $this->assertFalse($status['available']);
        $this->assertEquals('unknown', $status['storage_type']);
        $this->assertFalse($status['storage_available']);
        $this->assertEmpty($status['storage_info']);
    }

    public function test_get_file_info(): void
    {
        $storagePath = 'uploads/user123/2024/08/12/uuid-song.wav';
        $expectedInfo = [
            'exists' => true,
            'size_bytes' => 5242880,
            'format' => 'wav',
        ];

        $this->mockClient->expects($this->once())
            ->method('getFileInfo')
            ->with($storagePath)
            ->willReturn($expectedInfo);

        $result = $this->analysisService->getFileInfo($storagePath);

        $this->assertEquals($expectedInfo, $result);
    }

    public function test_list_files(): void
    {
        $prefix = 'uploads/user123/';
        $expectedFiles = [
            'files' => ['file1.wav', 'file2.wav'],
            'total_count' => 2,
        ];

        $this->mockClient->expects($this->once())
            ->method('listFiles')
            ->with($prefix, 100)
            ->willReturn($expectedFiles);

        $result = $this->analysisService->listFiles($prefix, 100);

        $this->assertEquals($expectedFiles, $result);
    }

    public function test_delete_task_successfully(): void
    {
        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
            'progress' => 50,
        ]);

        $this->mockClient->expects($this->once())
            ->method('deleteTask')
            ->with('test-task-123')
            ->willReturn([
                'task_id' => 'test-task-123',
                'status' => 'deleted',
                'message' => 'Task deleted successfully',
            ]);

        $result = $this->analysisService->deleteTask($task);

        $this->assertTrue($result);
        $task->refresh();
        $this->assertEquals('deleted', $task->status);
        $this->assertEquals('Task deleted by user', $task->error_message);
    }

    public function test_delete_task_removes_existing_analysis(): void
    {
        // Create analysis data first
        $analysis = $this->upload->analysis()->create([
            'musical_key' => 'C major',
            'bpm' => 120,
        ]);

        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
        ]);

        $this->mockClient->expects($this->once())
            ->method('deleteTask')
            ->with('test-task-123')
            ->willReturn(['status' => 'deleted']);

        $result = $this->analysisService->deleteTask($task);

        $this->assertTrue($result);

        // Check that analysis was deleted
        $this->upload->refresh();
        $this->assertNull($this->upload->analysis);
        $this->assertDatabaseMissing('upload_analyses', ['id' => $analysis->id]);
    }

    public function test_delete_task_handles_microservice_failure(): void
    {
        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'processing',
        ]);

        $this->mockClient->expects($this->once())
            ->method('deleteTask')
            ->with('test-task-123')
            ->willThrowException(new \Exception('Microservice error'));

        $result = $this->analysisService->deleteTask($task);

        $this->assertFalse($result);
        $task->refresh();
        $this->assertEquals('deleted', $task->status);
        $this->assertStringContainsString('Task deletion failed', $task->error_message);
    }

    public function test_delete_task_for_failed_task(): void
    {
        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'failed',
            'error_message' => 'Original failure reason',
        ]);

        $this->mockClient->expects($this->once())
            ->method('deleteTask')
            ->with('test-task-123')
            ->willReturn(['status' => 'deleted']);

        $result = $this->analysisService->deleteTask($task);

        $this->assertTrue($result);
        $task->refresh();
        $this->assertEquals('deleted', $task->status);
        $this->assertEquals('Task deleted by user', $task->error_message);
    }

    public function test_delete_task_for_pending_task(): void
    {
        $task = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'test-task-123',
            'status' => 'pending',
            'progress' => 0,
        ]);

        $this->mockClient->expects($this->once())
            ->method('deleteTask')
            ->with('test-task-123')
            ->willReturn([
                'task_id' => 'test-task-123',
                'status' => 'deleted',
                'deleted_from_celery' => true,
                'marked_as_deleted' => true,
            ]);

        $result = $this->analysisService->deleteTask($task);

        $this->assertTrue($result);
        $task->refresh();
        $this->assertEquals('deleted', $task->status);
        $this->assertEquals('Task deleted by user', $task->error_message);
    }

    public function test_submit_for_analysis_removes_existing_deleted_task(): void
    {
        // Create a deleted task first
        $deletedTask = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'deleted-task-123',
            'status' => 'deleted',
            'error_message' => 'Task deleted by user',
        ]);

        $this->mockClient->expects($this->once())
            ->method('extractFeatures')
            ->willReturn([
                'task_id' => 'new-task-456',
                'status' => 'pending',
            ]);

        $newTask = $this->analysisService->submitForAnalysis($this->upload);

        $this->assertNotNull($newTask);
        $this->assertEquals('new-task-456', $newTask->task_id);
        $this->assertEquals('pending', $newTask->status);

        // Verify old deleted task was removed
        $this->assertDatabaseMissing('upload_analysis_tasks', ['id' => $deletedTask->id]);
    }

    public function test_submit_for_analysis_removes_existing_failed_task(): void
    {
        // Create a failed task first
        $failedTask = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'failed-task-123',
            'status' => 'failed',
            'error_message' => 'Analysis failed',
        ]);

        $this->mockClient->expects($this->once())
            ->method('extractFeatures')
            ->willReturn([
                'task_id' => 'new-task-789',
                'status' => 'pending',
            ]);

        $newTask = $this->analysisService->submitForAnalysis($this->upload);

        $this->assertNotNull($newTask);
        $this->assertEquals('new-task-789', $newTask->task_id);
        $this->assertEquals('pending', $newTask->status);

        // Verify old failed task was removed
        $this->assertDatabaseMissing('upload_analysis_tasks', ['id' => $failedTask->id]);
    }

    public function test_submit_for_analysis_keeps_processing_task(): void
    {
        // Create a processing task
        $processingTask = UploadAnalysisTask::factory()->create([
            'upload_id' => $this->upload->id,
            'task_id' => 'processing-task-123',
            'status' => 'processing',
            'progress' => 50,
        ]);

        // Should not call extractFeatures since there's an active task
        $this->mockClient->expects($this->never())
            ->method('extractFeatures');

        $result = $this->analysisService->submitForAnalysis($this->upload);

        // Should return null since there's already a processing task
        $this->assertNull($result);

        // Verify processing task still exists
        $this->assertDatabaseHas('upload_analysis_tasks', ['id' => $processingTask->id]);
    }
}
