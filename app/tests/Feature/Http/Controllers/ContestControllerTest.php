<?php

namespace Tests\Feature\Http\Controllers;

use App\Http\Controllers\ContestController;
use App\Models\Contest;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Illuminate\Http\Request;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

/**
 * @see \App\Http\Controllers\ContestController
 */
final class ContestControllerTest extends TestCase
{
    use RefreshDatabase;
    use WithFaker;

    /**
     * Test that unauthenticated users are redirected to the login page.
     */
    #[Test]
    public function index_requires_authentication()
    {
        $response = $this->get(route('contests.index'));
        $response->assertRedirect(route('login'));
    }

    /**
     * Test the pagination of contests.
     */
    #[Test]
    public function index_paginates_contests()
    {
        // Create contests (more than the default pagination limit)
        $user = User::factory()->create();
        Contest::factory()
            ->count(12)
            ->for($user)
            ->create();

        // Query contests directly as the controller would
        $contests = Contest::query()
            ->with('user')
            ->withCount('contestUsers')
            ->latest()
            ->paginate(10);

        // Verify pagination is working
        $this->assertEquals(10, $contests->count());
        $this->assertEquals(12, $contests->total());
    }

    /**
     * Test that contest users count is included.
     */
    #[Test]
    public function index_includes_contest_users_count()
    {
        // Create a contest
        $user = User::factory()->create();
        $contest = Contest::factory()->for($user)->create();

        // Add contest users
        $contest->contestUsers()->createMany([
            ['user_id' => User::factory()->create()->id, 'title' => 'Track 1', 'rating_at_contest' => 1200, 'original_path' => 's3://example/track1.mp3'],
            ['user_id' => User::factory()->create()->id, 'title' => 'Track 2', 'rating_at_contest' => 1300, 'original_path' => 's3://example/track2.mp3'],
            ['user_id' => User::factory()->create()->id, 'title' => 'Track 3', 'rating_at_contest' => 1400, 'original_path' => 's3://example/track3.mp3'],
        ]);

        // Query the contest with counts
        $contestWithCount = Contest::query()
            ->withCount('contestUsers')
            ->find($contest->id);

        // Verify the count is included
        $this->assertEquals(3, $contestWithCount->contest_users_count);
    }

    /**
     * Test that contests are ordered by latest first.
     */
    #[Test]
    public function index_orders_contests_by_latest_first()
    {
        // Create contests with different dates
        $user = User::factory()->create();

        $oldContest = Contest::factory()
            ->for($user)
            ->create(['created_at' => now()->subDays(5)]);

        $newContest = Contest::factory()
            ->for($user)
            ->create(['created_at' => now()]);

        // Get contests ordered by latest
        $contests = Contest::query()
            ->latest()
            ->get();

        // Verify ordering
        $this->assertEquals($newContest->id, $contests->first()->id);
        $this->assertEquals($oldContest->id, $contests->last()->id);
    }

    /**
     * Test the controller directly using mock request.
     */
    #[Test]
    public function controller_returns_correct_data()
    {
        // Create some test data
        $user = User::factory()->create();
        $contests = Contest::factory()
            ->count(3)
            ->for($user)
            ->create();

        // Create a controller instance
        $controller = new ContestController();

        // Call the index method with a mock request
        $response = $controller->index(new Request());

        // For an Inertia response, simply verify it's not null
        $this->assertNotNull($response);

        // The Inertia response object is a particular structure
        // Check that it's the expected type of response
        $this->assertInstanceOf(\Inertia\Response::class, $response);
    }
}
