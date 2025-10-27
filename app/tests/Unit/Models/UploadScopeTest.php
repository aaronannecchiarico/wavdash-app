<?php

namespace Tests\Unit\Models;

use App\Models\Upload;
use App\Models\UploadAnalysis;
use App\Models\UploadAnalysisTask;
use App\Models\UploadStem;
use App\Models\UploadStemTask;
use App\Models\UploadTempo;
use App\Models\UploadTempoTask;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class UploadScopeTest extends TestCase
{
    use RefreshDatabase;

    #[Test]
    public function it_filters_by_completed_analysis_status(): void
    {
        $user = User::factory()->create();
        $withAnalysis = Upload::factory()->for($user)->create();
        UploadAnalysis::factory()->for($withAnalysis, 'upload')->create();

        $withoutAnalysis = Upload::factory()->for($user)->create();

        $results = Upload::withAnalysisStatus('completed')->get();

        $this->assertTrue($results->contains($withAnalysis));
        $this->assertFalse($results->contains($withoutAnalysis));
    }

    #[Test]
    public function it_filters_by_not_completed_analysis_status(): void
    {
        $user = User::factory()->create();
        $withAnalysis = Upload::factory()->for($user)->create();
        UploadAnalysis::factory()->for($withAnalysis, 'upload')->create();

        $withoutAnalysis = Upload::factory()->for($user)->create();

        $results = Upload::withAnalysisStatus('not_completed')->get();

        $this->assertFalse($results->contains($withAnalysis));
        $this->assertTrue($results->contains($withoutAnalysis));
    }

    #[Test]
    public function it_filters_by_in_progress_analysis_status(): void
    {
        $user = User::factory()->create();

        // Upload with in-progress analysis
        $inProgress = Upload::factory()->for($user)->create();
        UploadAnalysisTask::factory()->for($inProgress, 'upload')->create([
            'status' => 'processing',
        ]);

        // Upload with pending analysis
        $pending = Upload::factory()->for($user)->create();
        UploadAnalysisTask::factory()->for($pending, 'upload')->create([
            'status' => 'pending',
        ]);

        // Upload with completed analysis
        $completed = Upload::factory()->for($user)->create();
        UploadAnalysis::factory()->for($completed, 'upload')->create();

        $results = Upload::withAnalysisStatus('in_progress')->get();

        $this->assertTrue($results->contains($inProgress));
        $this->assertTrue($results->contains($pending));
        $this->assertFalse($results->contains($completed));
    }

    #[Test]
    public function it_returns_all_uploads_for_invalid_analysis_status(): void
    {
        $user = User::factory()->create();
        $upload1 = Upload::factory()->for($user)->create();
        $upload2 = Upload::factory()->for($user)->create();

        $results = Upload::withAnalysisStatus('invalid_status')->get();

        $this->assertCount(2, $results);
        $this->assertTrue($results->contains($upload1));
        $this->assertTrue($results->contains($upload2));
    }

    #[Test]
    public function it_filters_by_completed_stems_status(): void
    {
        $user = User::factory()->create();
        $withStems = Upload::factory()->for($user)->create();
        UploadStem::factory()->for($withStems, 'upload')->create();

        $withoutStems = Upload::factory()->for($user)->create();

        $results = Upload::withStemsStatus('completed')->get();

        $this->assertTrue($results->contains($withStems));
        $this->assertFalse($results->contains($withoutStems));
    }

    #[Test]
    public function it_filters_by_not_completed_stems_status(): void
    {
        $user = User::factory()->create();
        $withStems = Upload::factory()->for($user)->create();
        UploadStem::factory()->for($withStems, 'upload')->create();

        $withoutStems = Upload::factory()->for($user)->create();

        $results = Upload::withStemsStatus('not_completed')->get();

        $this->assertFalse($results->contains($withStems));
        $this->assertTrue($results->contains($withoutStems));
    }

    #[Test]
    public function it_filters_by_in_progress_stems_status(): void
    {
        $user = User::factory()->create();

        // Upload with in-progress stem task
        $inProgress = Upload::factory()->for($user)->create();
        UploadStemTask::factory()->for($inProgress, 'upload')->create([
            'status' => 'processing',
        ]);

        // Upload with pending stem task
        $pending = Upload::factory()->for($user)->create();
        UploadStemTask::factory()->for($pending, 'upload')->create([
            'status' => 'pending',
        ]);

        // Upload with completed stems
        $completed = Upload::factory()->for($user)->create();
        UploadStem::factory()->for($completed, 'upload')->create();

        $results = Upload::withStemsStatus('in_progress')->get();

        $this->assertTrue($results->contains($inProgress));
        $this->assertTrue($results->contains($pending));
        $this->assertFalse($results->contains($completed));
    }

    #[Test]
    public function it_filters_by_completed_tempo_status(): void
    {
        $user = User::factory()->create();
        $withTempos = Upload::factory()->for($user)->create();
        UploadTempo::factory()->for($withTempos, 'upload')->create();

        $withoutTempos = Upload::factory()->for($user)->create();

        $results = Upload::withTempoStatus('completed')->get();

        $this->assertTrue($results->contains($withTempos));
        $this->assertFalse($results->contains($withoutTempos));
    }

    #[Test]
    public function it_filters_by_not_completed_tempo_status(): void
    {
        $user = User::factory()->create();
        $withTempos = Upload::factory()->for($user)->create();
        UploadTempo::factory()->for($withTempos, 'upload')->create();

        $withoutTempos = Upload::factory()->for($user)->create();

        $results = Upload::withTempoStatus('not_completed')->get();

        $this->assertFalse($results->contains($withTempos));
        $this->assertTrue($results->contains($withoutTempos));
    }

    #[Test]
    public function it_filters_by_in_progress_tempo_status(): void
    {
        $user = User::factory()->create();

        // Upload with in-progress tempo task
        $inProgress = Upload::factory()->for($user)->create();
        UploadTempoTask::factory()->for($inProgress, 'upload')->create([
            'status' => 'processing',
        ]);

        // Upload with pending tempo task
        $pending = Upload::factory()->for($user)->create();
        UploadTempoTask::factory()->for($pending, 'upload')->create([
            'status' => 'pending',
        ]);

        // Upload with completed tempos
        $completed = Upload::factory()->for($user)->create();
        UploadTempo::factory()->for($completed, 'upload')->create();

        $results = Upload::withTempoStatus('in_progress')->get();

        $this->assertTrue($results->contains($inProgress));
        $this->assertTrue($results->contains($pending));
        $this->assertFalse($results->contains($completed));
    }

    #[Test]
    public function it_applies_custom_sorting_by_title_asc(): void
    {
        $user = User::factory()->create();
        $uploadZ = Upload::factory()->withoutFiles()->for($user)->create(['title' => 'Z Track']);
        $uploadA = Upload::factory()->withoutFiles()->for($user)->create(['title' => 'A Track']);
        $uploadM = Upload::factory()->withoutFiles()->for($user)->create(['title' => 'M Track']);

        $results = Upload::userSort('title', 'asc')->get();

        $this->assertCount(3, $results);
        $this->assertTrue($results->first()->is($uploadA));
        $this->assertTrue($results->get(1)->is($uploadM));
        $this->assertTrue($results->last()->is($uploadZ));
    }

    #[Test]
    public function it_applies_custom_sorting_by_title_desc(): void
    {
        $user = User::factory()->create();
        $uploadA = Upload::factory()->withoutFiles()->for($user)->create(['title' => 'A Track']);
        $uploadZ = Upload::factory()->withoutFiles()->for($user)->create(['title' => 'Z Track']);
        $uploadM = Upload::factory()->withoutFiles()->for($user)->create(['title' => 'M Track']);

        $results = Upload::userSort('title', 'desc')->get();

        $this->assertCount(3, $results);
        $this->assertTrue($results->first()->is($uploadZ));
        $this->assertTrue($results->get(1)->is($uploadM));
        $this->assertTrue($results->last()->is($uploadA));
    }

    #[Test]
    public function it_applies_custom_sorting_by_size(): void
    {
        $user = User::factory()->create();
        $uploadLarge = Upload::factory()->withoutFiles()->for($user)->create(['size' => 3000000]);
        $uploadSmall = Upload::factory()->withoutFiles()->for($user)->create(['size' => 1000000]);
        $uploadMedium = Upload::factory()->withoutFiles()->for($user)->create(['size' => 2000000]);

        $results = $user->uploads()->userSort('size', 'asc')->get();

        $this->assertCount(3, $results);
        $this->assertTrue($results->first()->is($uploadSmall));
        $this->assertTrue($results->get(1)->is($uploadMedium));
        $this->assertTrue($results->last()->is($uploadLarge));
    }

    #[Test]
    public function it_applies_custom_sorting_by_duration(): void
    {
        $user = User::factory()->create();
        $uploadLong = Upload::factory()->withoutFiles()->for($user)->create(['duration_seconds' => 300]);
        $uploadShort = Upload::factory()->withoutFiles()->for($user)->create(['duration_seconds' => 100]);
        $uploadMedium = Upload::factory()->withoutFiles()->for($user)->create(['duration_seconds' => 200]);

        $results = $user->uploads()->userSort('duration', 'asc')->get();

        $this->assertCount(3, $results);
        $this->assertTrue($results->first()->is($uploadShort));
        $this->assertTrue($results->get(1)->is($uploadMedium));
        $this->assertTrue($results->last()->is($uploadLong));
    }

    #[Test]
    public function it_applies_custom_sorting_by_updated_at(): void
    {
        $user = User::factory()->create();
        $upload1 = Upload::factory()->withoutFiles()->for($user)->create(['updated_at' => now()->subDays(3)]);
        $upload2 = Upload::factory()->withoutFiles()->for($user)->create(['updated_at' => now()->subDay()]);
        $upload3 = Upload::factory()->withoutFiles()->for($user)->create(['updated_at' => now()]);

        $results = $user->uploads()->userSort('updated_at', 'desc')->get();

        $this->assertCount(3, $results);
        $this->assertTrue($results->first()->is($upload3));
        $this->assertTrue($results->get(1)->is($upload2));
        $this->assertTrue($results->last()->is($upload1));
    }

    #[Test]
    public function it_defaults_to_latest_updated_for_invalid_sort_column(): void
    {
        $user = User::factory()->create();
        $older = Upload::factory()->withoutFiles()->for($user)->create(['updated_at' => now()->subDay()]);
        $latest = Upload::factory()->withoutFiles()->for($user)->create(['updated_at' => now()]);

        $results = $user->uploads()->userSort('invalid_column', 'asc')->get();

        $this->assertCount(2, $results);
        $this->assertTrue($results->first()->is($latest));
        $this->assertTrue($results->last()->is($older));
    }

    #[Test]
    public function it_defaults_to_latest_updated_for_disallowed_sort_column(): void
    {
        $user = User::factory()->create();
        $older = Upload::factory()->withoutFiles()->for($user)->create(['updated_at' => now()->subDay()]);
        $latest = Upload::factory()->withoutFiles()->for($user)->create(['updated_at' => now()]);

        // Attempt to sort by a column that exists but isn't in allowed list
        $results = $user->uploads()->userSort('id', 'asc')->get();

        $this->assertCount(2, $results);
        $this->assertTrue($results->first()->is($latest));
        $this->assertTrue($results->last()->is($older));
    }

    #[Test]
    public function it_can_chain_multiple_scopes_together(): void
    {
        $user = User::factory()->create();

        // Create upload with analysis but no stems
        $withAnalysis = Upload::factory()->for($user)->create(['title' => 'A Track']);
        UploadAnalysis::factory()->for($withAnalysis, 'upload')->create();

        // Create upload with stems but no analysis
        $withStems = Upload::factory()->for($user)->create(['title' => 'Z Track']);
        UploadStem::factory()->for($withStems, 'upload')->create();

        // Create upload with both
        $withBoth = Upload::factory()->for($user)->create(['title' => 'M Track']);
        UploadAnalysis::factory()->for($withBoth, 'upload')->create();
        UploadStem::factory()->for($withBoth, 'upload')->create();

        // Query for uploads with both analysis AND stems, sorted by title
        $results = Upload::query()
            ->withAnalysisStatus('completed')
            ->withStemsStatus('completed')
            ->userSort('title', 'asc')
            ->get();

        $this->assertCount(1, $results);
        $this->assertEquals($withBoth->id, $results->first()->id);
    }

    #[Test]
    public function it_can_scope_to_user_uploads_with_filters(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();

        // User 1 uploads
        $user1Upload1 = Upload::factory()->for($user1)->create(['title' => 'User 1 Track 1']);
        UploadAnalysis::factory()->for($user1Upload1, 'upload')->create();

        $user1Upload2 = Upload::factory()->for($user1)->create(['title' => 'User 1 Track 2']);

        // User 2 uploads
        $user2Upload1 = Upload::factory()->for($user2)->create(['title' => 'User 2 Track 1']);
        UploadAnalysis::factory()->for($user2Upload1, 'upload')->create();

        // Query user 1's uploads with completed analysis
        $results = $user1->uploads()
            ->withAnalysisStatus('completed')
            ->get();

        $this->assertCount(1, $results);
        $this->assertEquals($user1Upload1->id, $results->first()->id);
    }
}
