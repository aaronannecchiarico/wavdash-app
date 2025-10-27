<?php

namespace Tests\Unit;

use App\Services\AudioMicroserviceClient;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class AudioMicroserviceClientTest extends TestCase
{
    use RefreshDatabase;

    private AudioMicroserviceClient $client;

    protected function setUp(): void
    {
        parent::setUp();
        Config::set('services.audio_analysis.base_url', 'http://localhost:8001');
        $this->client = new AudioMicroserviceClient;
    }

    public function test_extract_features_makes_correct_api_call(): void
    {
        Http::fake([
            'localhost:8001/storage/extract-features' => Http::response([
                'task_id' => 'test-task-123',
                'status' => 'processing',
                'message' => 'Task submitted successfully',
            ]),
        ]);

        $storagePath = 'uploads/user123/2024/08/12/uuid-song.wav';
        $options = [
            'detailed' => false,
            'callback_url' => 'https://app.test/api/audio/analysis/callback/123',
            'metadata' => [
                'upload_id' => 123,
                'user_id' => 456,
                'original_filename' => 'song.wav',
            ],
        ];

        $result = $this->client->extractFeatures($storagePath, $options);

        Http::assertSent(function ($request) use ($storagePath, $options) {
            $data = $request->data();

            return $request->url() === 'http://localhost:8001/storage/extract-features' &&
                   $data['storage_path'] === $storagePath &&
                   $data['extract_detailed'] === false &&
                   $data['callback_url'] === $options['callback_url'] &&
                   $data['metadata'] === $options['metadata'];
        });

        $this->assertEquals('test-task-123', $result['task_id']);
        $this->assertEquals('processing', $result['status']);
    }

    public function test_extract_features_handles_api_failure(): void
    {
        Http::fake([
            'localhost:8001/storage/extract-features' => Http::response([
                'error' => 'File not found',
            ], 404),
        ]);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Microservice error:');

        $this->client->extractFeatures('uploads/nonexistent.wav');
    }

    public function test_separate_stems_makes_correct_api_call(): void
    {
        Http::fake([
            'localhost:8001/storage/separate-stems' => Http::response([
                'task_id' => 'stem-task-456',
                'status' => 'processing',
                'estimated_time' => 120,
            ]),
        ]);

        $storagePath = 'uploads/user123/2024/08/12/uuid-song.wav';
        $options = [
            'model' => 'htdemucs',
            'callback_url' => 'https://app.test/api/stems/callback/123',
            'metadata' => ['upload_id' => 123],
        ];

        $result = $this->client->separateStems($storagePath, $options);

        Http::assertSent(function ($request) use ($storagePath, $options) {
            $data = $request->data();

            return $request->url() === 'http://localhost:8001/storage/separate-stems' &&
                   $data['storage_path'] === $storagePath &&
                   $data['model_name'] === 'htdemucs' &&
                   $data['callback_url'] === $options['callback_url'] &&
                   $data['metadata'] === $options['metadata'];
        });

        $this->assertEquals('stem-task-456', $result['task_id']);
    }

    public function test_get_task_summary(): void
    {
        Http::fake([
            'localhost:8001/task-summary/test-task-123' => Http::response([
                'task_id' => 'test-task-123',
                'status' => 'completed',
                'analysis_summary' => [
                    'bpm' => 120.5,
                    'key' => 'C major',
                    'key_confidence' => 0.85,
                    'loudness_db' => -12.3,
                ],
                'processing_time' => 3.45,
            ]),
        ]);

        $result = $this->client->getTaskSummary('test-task-123');

        $this->assertEquals('test-task-123', $result['task_id']);
        $this->assertEquals('completed', $result['status']);
        $this->assertEquals(120.5, $result['analysis_summary']['bpm']);
        $this->assertEquals('C major', $result['analysis_summary']['key']);
    }

    public function test_get_task_status(): void
    {
        Http::fake([
            'localhost:8001/task-status/test-task-123' => Http::response([
                'task_id' => 'test-task-123',
                'status' => 'processing',
                'progress' => 75,
            ]),
        ]);

        $result = $this->client->getTaskStatus('test-task-123');

        $this->assertEquals('test-task-123', $result['task_id']);
        $this->assertEquals('processing', $result['status']);
        $this->assertEquals(75, $result['progress']);
    }

    public function test_get_storage_status(): void
    {
        Http::fake([
            'localhost:8001/storage/status' => Http::response([
                'storage_type' => 'local',
                'available' => true,
                'storage_path' => '/path/to/laravel/storage/app',
                'total_files' => 42,
                'total_size_bytes' => 1073741824,
            ]),
        ]);

        $result = $this->client->getStorageStatus();

        $this->assertEquals('local', $result['storage_type']);
        $this->assertTrue($result['available']);
        $this->assertEquals(42, $result['total_files']);
    }

    public function test_is_service_available_when_healthy(): void
    {
        Http::fake([
            'localhost:8001/health' => Http::response([
                'status' => 'healthy',
                'timestamp' => now()->toISOString(),
            ]),
        ]);

        $this->assertTrue($this->client->isServiceAvailable());
    }

    public function test_is_service_available_when_unhealthy(): void
    {
        Http::fake([
            'localhost:8001/health' => Http::response([
                'status' => 'unhealthy',
            ], 500),
        ]);

        $this->assertFalse($this->client->isServiceAvailable());
    }

    public function test_is_service_available_when_unreachable(): void
    {
        Http::fake([
            'localhost:8001/health' => Http::response([], 500),
        ]);

        $this->assertFalse($this->client->isServiceAvailable());
    }

    public function test_get_file_info(): void
    {
        Http::fake([
            'localhost:8001/storage/file-info/*' => Http::response([
                'storage_path' => 'uploads/user123/2024/08/12/uuid-song.wav',
                'exists' => true,
                'size_bytes' => 5242880,
                'format' => 'wav',
                'duration' => 180.0,
                'sample_rate' => 44100,
            ]),
        ]);

        $result = $this->client->getFileInfo('uploads/user123/2024/08/12/uuid-song.wav');

        $this->assertTrue($result['exists']);
        $this->assertEquals(5242880, $result['size_bytes']);
        $this->assertEquals('wav', $result['format']);
        $this->assertEquals(180.0, $result['duration']);
    }

    public function test_list_files(): void
    {
        Http::fake([
            'localhost:8001/storage/list-files*' => Http::response([
                'files' => [
                    'uploads/user123/2024/08/12/uuid1-song1.wav',
                    'uploads/user123/2024/08/12/uuid2-song2.wav',
                ],
                'total_count' => 2,
                'prefix' => 'uploads/user123/',
                'storage_type' => 'local',
            ]),
        ]);

        $result = $this->client->listFiles('uploads/user123/', 100);

        $this->assertCount(2, $result['files']);
        $this->assertEquals(2, $result['total_count']);
        $this->assertEquals('local', $result['storage_type']);
    }

    public function test_delete_task_makes_correct_api_call(): void
    {
        Http::fake([
            'localhost:8001/task/test-task-123' => Http::response([
                'task_id' => 'test-task-123',
                'status' => 'deleted',
                'message' => 'Task deleted successfully',
                'deleted_from_celery' => true,
                'marked_as_deleted' => true,
            ]),
        ]);

        $result = $this->client->deleteTask('test-task-123');

        Http::assertSent(function ($request) {
            return $request->method() === 'DELETE' &&
                   $request->url() === 'http://localhost:8001/task/test-task-123';
        });

        $this->assertEquals('test-task-123', $result['task_id']);
        $this->assertEquals('deleted', $result['status']);
        $this->assertTrue($result['deleted_from_celery']);
        $this->assertTrue($result['marked_as_deleted']);
    }

    public function test_delete_task_handles_api_failure(): void
    {
        Http::fake([
            'localhost:8001/task/test-task-123' => Http::response([
                'error' => 'Task not found',
            ], 404),
        ]);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Failed to delete task:');

        $this->client->deleteTask('test-task-123');
    }

    public function test_delete_task_handles_service_error(): void
    {
        Http::fake([
            'localhost:8001/task/test-task-123' => Http::response([
                'error' => 'Internal server error',
            ], 500),
        ]);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Failed to delete task:');

        $this->client->deleteTask('test-task-123');
    }
}
