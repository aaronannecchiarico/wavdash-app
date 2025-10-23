<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class HomeRouteRedirectTest extends TestCase
{
    use RefreshDatabase;

    /**
     * Test that unauthenticated users are redirected to the marketing site
     */
    public function test_unauthenticated_users_redirected_to_marketing_site(): void
    {
        // Set marketing URL for testing
        config(['app.marketing_url' => 'https://wavdash.com']);

        $response = $this->get('/');

        $response->assertRedirect('https://wavdash.com');
    }

    /**
     * Test that authenticated users are redirected to the dashboard
     */
    public function test_authenticated_users_redirected_to_dashboard(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get('/');

        $response->assertRedirect(route('dashboard'));
    }

    /**
     * Test that the marketing URL can be configured via environment
     */
    public function test_marketing_url_respects_configuration(): void
    {
        // Set custom marketing URL for testing
        $customUrl = 'http://localhost:4321';
        config(['app.marketing_url' => $customUrl]);

        $response = $this->get('/');

        $response->assertRedirect($customUrl);
    }
}
