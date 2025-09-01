<?php

namespace Tests\Feature;

use App\Models\FailedJob;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Spatie\Permission\Models\Role;
use Tests\TestCase;

class AdminFailedJobAccessTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Reset cached roles and permissions
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();

        // Create SuperAdmin role for tests
        Role::firstOrCreate(['name' => 'SuperAdmin']);
    }

    public function test_super_admin_can_access_failed_jobs_list_in_admin_panel(): void
    {
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        $this->createFailedJob();

        $response = $this->actingAs($superAdmin)
            ->get('/admin/failed-jobs');

        $response->assertSuccessful();
    }

    public function test_regular_user_cannot_access_admin_panel_failed_jobs(): void
    {
        $regularUser = User::factory()->create();

        $response = $this->actingAs($regularUser)
            ->get('/admin/failed-jobs');

        // Should be blocked by the admin middleware (redirect or 403)
        $this->assertContains($response->getStatusCode(), [302, 403, 404]);
    }

    /**
     * Create a test failed job record
     */
    private function createFailedJob(): FailedJob
    {
        return FailedJob::create([
            'uuid' => 'test-uuid-' . uniqid(),
            'connection' => 'database',
            'queue' => 'default',
            'payload' => json_encode([
                'displayName' => 'App\\Jobs\\TestJob',
                'job' => 'serialized-job-data',
                'data' => ['test' => 'data']
            ]),
            'exception' => 'Test exception message for failed job',
            'failed_at' => now(),
        ]);
    }
}
