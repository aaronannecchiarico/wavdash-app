<?php

namespace Tests\Unit;

use App\Models\Upload;
use App\Models\UploadStem;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class UploadStemTest extends TestCase
{
    use RefreshDatabase;

    public function test_it_can_be_created_with_required_fields(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $stem = UploadStem::create([
            'upload_id' => $upload->id,
            'stem_type' => 'vocals',
            'file_path' => 'uploads/stems/test.wav',
            'storage_type' => 'r2',
            'file_size' => 1024000,
            'duration' => 180.5,
        ]);

        $this->assertInstanceOf(UploadStem::class, $stem);
        $this->assertEquals($upload->id, $stem->upload_id);
        $this->assertEquals('vocals', $stem->stem_type);
        $this->assertEquals('uploads/stems/test.wav', $stem->file_path);
        $this->assertEquals('r2', $stem->storage_type);
        $this->assertEquals(1024000, $stem->file_size);
        $this->assertEquals(180.5, $stem->duration);
    }

    public function test_it_belongs_to_an_upload(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);
        $stem = UploadStem::factory()->create(['upload_id' => $upload->id]);

        $this->assertInstanceOf(Upload::class, $stem->upload);
        $this->assertEquals($upload->id, $stem->upload->id);
    }

    public function test_it_returns_correct_stem_type_names(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $vocalsStep = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'vocals',
        ]);

        $drumsStep = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'drums',
        ]);

        $bassStep = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'bass',
        ]);

        $otherStep = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'other',
        ]);

        $this->assertEquals('Vocals', $vocalsStep->getStemTypeName());
        $this->assertEquals('Drums', $drumsStep->getStemTypeName());
        $this->assertEquals('Bass', $bassStep->getStemTypeName());
        $this->assertEquals('Other Instruments', $otherStep->getStemTypeName());
    }

    public function test_it_formats_file_size_correctly(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $smallStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'vocals',
            'file_size' => 1024, // 1KB
        ]);

        $mediumStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'drums',
            'file_size' => 1048576, // 1MB
        ]);

        $largeStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'bass',
            'file_size' => 1073741824, // 1GB
        ]);

        $nullStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'other',
            'file_size' => null,
        ]);

        $this->assertEquals('1 KB', $smallStem->getFormattedFileSize());
        $this->assertEquals('1 MB', $mediumStem->getFormattedFileSize());
        $this->assertEquals('1 GB', $largeStem->getFormattedFileSize());
        $this->assertEquals('Unknown size', $nullStem->getFormattedFileSize());
    }

    public function test_it_formats_duration_correctly(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $shortStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'vocals',
            'duration' => 65.5, // 1 minute 5.5 seconds
        ]);

        $longStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'drums',
            'duration' => 3661.2, // 1 hour 1 minute 1.2 seconds
        ]);

        $nullStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'bass',
            'duration' => null,
        ]);

        $this->assertEquals('1:05', $shortStem->getFormattedDuration());
        $this->assertEquals('61:01', $longStem->getFormattedDuration());
        $this->assertEquals('Unknown duration', $nullStem->getFormattedDuration());
    }

    public function test_it_can_check_storage_type(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        $localStem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'vocals',
            'storage_type' => 'local',
        ]);

        $r2Stem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'drums',
            'storage_type' => 'r2',
        ]);

        $this->assertTrue($localStem->isStoredLocally());
        $this->assertFalse($localStem->isStoredOnR2());

        $this->assertFalse($r2Stem->isStoredLocally());
        $this->assertTrue($r2Stem->isStoredOnR2());
    }

    public function test_it_casts_attributes_correctly(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);
        $stem = UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'file_size' => '1048576',
            'duration' => '180.5',
            'metadata' => ['key' => 'value'],
        ]);

        $this->assertIsInt($stem->id);
        $this->assertIsInt($stem->upload_id);
        $this->assertIsInt($stem->file_size);
        $this->assertIsFloat($stem->duration);
        $this->assertIsArray($stem->metadata);
    }

    public function test_it_enforces_unique_stem_type_per_upload(): void
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);

        // Create the first vocals stem
        UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'vocals',
        ]);

        // Try to create another vocals stem for the same upload - should fail
        $this->expectException(\Exception::class);

        UploadStem::factory()->create([
            'upload_id' => $upload->id,
            'stem_type' => 'vocals',
        ]);
    }
}
