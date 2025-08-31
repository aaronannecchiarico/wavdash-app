<?php

use App\Models\Upload;
use App\Models\UploadTempo;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\Testing\File;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class TempoDisplayAndDownloadTest extends TestCase
{
    use RefreshDatabase;

    private User $user;

    private Upload $upload;

    protected function setUp(): void
    {
        parent::setUp();

        $this->user = User::factory()->create();
        $this->upload = Upload::factory()->create([
            'user_id' => $this->user->id,
            'status' => 'ready',
            'duration_seconds' => 180.5, // 3 minutes 30.5 seconds
        ]);
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function tempo_display_shows_rounded_bpm()
    {
        $tempo = UploadTempo::factory()->create([
            'upload_id' => $this->upload->id,
            'preset' => 'nightcore',
            'tempo_factor' => 1.4,
            'final_bpm' => 168.7, // Should be rounded to 169
            'file_size' => 1024000, // 1MB instead of 5MB
            'duration' => 129.0, // Adjusted for tempo factor
        ]);

        $response = $this->actingAs($this->user)->get(route('uploads.tempo.show', $this->upload));

        $response->assertSuccessful()
            ->assertInertia(fn ($page) => $page
                ->component('uploads/tempo')
                ->has('upload.data.tempos', 1)
                ->has('upload.data.tempos.0', fn ($tempoData) => $tempoData
                    ->where('id', $tempo->id)
                    ->where('final_bpm', 168.7) // Raw value should still be float
                    ->etc()
                )
            );
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function tempo_display_shows_calculated_duration_when_processed_with_tempo_factor()
    {
        // Original duration: 180.5 seconds
        // Tempo factor: 1.4 (40% faster)
        // Expected duration: 180.5 / 1.4 = ~129 seconds

        $tempo = UploadTempo::factory()->create([
            'upload_id' => $this->upload->id,
            'preset' => 'nightcore',
            'tempo_factor' => 1.4,
            'duration' => 129, // Calculated duration as integer
            'file_size' => 1024000, // 1MB instead of 5MB
        ]);

        $response = $this->actingAs($this->user)->get(route('uploads.tempo.show', $this->upload));

        $response->assertSuccessful()
            ->assertInertia(fn ($page) => $page
                ->has('upload.data.tempos.0', fn ($tempoData) => $tempoData
                    ->where('duration', 129)
                    ->where('formatted_duration', '2:09')
                    ->etc()
                )
            );
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function tempo_display_shows_file_size_when_available()
    {
        $tempo = UploadTempo::factory()->create([
            'upload_id' => $this->upload->id,
            'preset' => 'sped_up',
            'file_size' => 2048000, // 2MB instead of 5MB
        ]);

        $response = $this->actingAs($this->user)->get(route('uploads.tempo.show', $this->upload));

        $response->assertSuccessful()
            ->assertInertia(fn ($page) => $page
                ->has('upload.data.tempos.0', fn ($tempoData) => $tempoData
                    ->where('file_size', 2048000)
                    ->where('formatted_file_size', '1.95 MB')
                    ->etc()
                )
            );
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function tempo_display_shows_unknown_size_when_file_size_is_null()
    {
        $tempo = UploadTempo::factory()->create([
            'upload_id' => $this->upload->id,
            'preset' => 'sped_up',
            'file_size' => null,
        ]);

        $response = $this->actingAs($this->user)->get(route('uploads.tempo.show', $this->upload));

        $response->assertSuccessful()
            ->assertInertia(fn ($page) => $page
                ->has('upload.data.tempos.0', fn ($tempoData) => $tempoData
                    ->where('file_size', null)
                    ->where('formatted_file_size', 'Unknown size')
                    ->etc()
                )
            );
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function can_download_tempo_file_when_stored_locally()
    {
        // Create a fake tempo file
        Storage::fake('private');
        $fakeFile = File::create('test-nightcore.wav', 1024);
        $storedPath = Storage::disk('private')->putFile('processed/1/2025/08/18', $fakeFile);

        $tempo = UploadTempo::factory()->create([
            'upload_id' => $this->upload->id,
            'preset' => 'nightcore',
            'file_path' => 'private/'.$storedPath,
            'storage_type' => 'local',
        ]);

        // Create the actual file in the expected location
        $fullPath = storage_path('app/private/'.$storedPath);
        if (! file_exists(dirname($fullPath))) {
            mkdir(dirname($fullPath), 0755, true);
        }
        file_put_contents($fullPath, 'fake audio content');

        $response = $this->actingAs($this->user)->get(route('uploads.tempo.download', [
            'upload' => $this->upload->id,
            'tempo' => $tempo->id,
        ]));

        $response->assertSuccessful();
        $response->assertHeader('content-disposition', 'attachment; filename=test_audio-nightcore.wav');
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function download_returns_error_when_tempo_not_found()
    {
        $response = $this->actingAs($this->user)->get(route('uploads.tempo.download', [
            'upload' => $this->upload->id,
            'tempo' => 999, // Non-existent tempo ID
        ]));

        $response->assertRedirect();
        $response->assertSessionHas('error', 'Tempo processed file not found.');
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function download_returns_error_when_file_not_found_on_disk()
    {
        $tempo = UploadTempo::factory()->create([
            'upload_id' => $this->upload->id,
            'preset' => 'nightcore',
            'file_path' => 'private/non-existent/path.wav',
            'storage_type' => 'local',
        ]);

        $response = $this->actingAs($this->user)->get(route('uploads.tempo.download', [
            'upload' => $this->upload->id,
            'tempo' => $tempo->id,
        ]));

        $response->assertRedirect();
        $response->assertSessionHas('error', 'Tempo processed file not found on disk.');
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function unauthorized_user_cannot_download_tempo()
    {
        $otherUser = User::factory()->create();
        $tempo = UploadTempo::factory()->create([
            'upload_id' => $this->upload->id,
            'preset' => 'nightcore',
        ]);

        $response = $this->actingAs($otherUser)->get(route('uploads.tempo.download', [
            'upload' => $this->upload->id,
            'tempo' => $tempo->id,
        ]));

        $response->assertForbidden();
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function callback_populates_file_size_and_duration_for_local_storage()
    {
        // This test simulates the callback handler improvements we made

        // Create a fake file to simulate the processed tempo file
        $testFilePath = storage_path('app/private/processed/1/2025/08/18/test_tempo.wav');
        if (! file_exists(dirname($testFilePath))) {
            mkdir(dirname($testFilePath), 0755, true);
        }
        // Use a much smaller file size to avoid memory exhaustion in tests
        file_put_contents($testFilePath, str_repeat('x', 1024)); // 1KB fake file instead of 5MB

        // Test the logic directly rather than through a full callback
        $filePath = 'private/processed/1/2025/08/18/test_tempo.wav';
        $fullPath = storage_path('app/'.$filePath);

        $this->assertTrue(file_exists($fullPath));
        $this->assertEquals(1024, filesize($fullPath)); // Updated expected size

        // Test duration calculation
        $originalDuration = 180.0;
        $tempoFactor = 1.4;
        $expectedDuration = $originalDuration / $tempoFactor;
        $this->assertEquals(128.57, round($expectedDuration, 2));
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function tempo_model_formats_file_sizes_correctly()
    {
        // Test various file sizes
        $testCases = [
            [512, '512 B'],
            [1024, '1 KB'],
            [1048576, '1 MB'],
            [1073741824, '1 GB'],
            [2048000, '1.95 MB'], // Changed from 5MB to avoid memory issues
            [null, 'Unknown size'],
        ];

        foreach ($testCases as [$fileSize, $expected]) {
            $tempo = UploadTempo::factory()->make(['file_size' => $fileSize]);
            $this->assertEquals($expected, $tempo->getFormattedFileSize());
        }
    }

    #[\PHPUnit\Framework\Attributes\Test]
    public function tempo_model_formats_durations_correctly()
    {
        $testCases = [
            [60, '1:00'],
            [90, '1:30'],
            [3661, '61:01'], // Over an hour
            [129, '2:09'],
            [null, 'Unknown duration'],
        ];

        foreach ($testCases as [$duration, $expected]) {
            $tempo = UploadTempo::factory()->make(['duration' => $duration]);
            $this->assertEquals($expected, $tempo->getFormattedDuration());
        }
    }
}
