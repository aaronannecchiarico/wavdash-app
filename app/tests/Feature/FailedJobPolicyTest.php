<?php

namespace Tests\Feature;

use App\Models\FailedJob;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Spatie\Permission\Models\Role;
use Tests\TestCase;

class FailedJobPolicyTest extends TestCase
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

    public function test_super_admin_can_view_any_failed_jobs(): void
    {
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        $this->assertTrue($superAdmin->can('viewAny', FailedJob::class));
    }

    public function test_regular_user_cannot_view_any_failed_jobs(): void
    {
        $regularUser = User::factory()->create();

        $this->assertFalse($regularUser->can('viewAny', FailedJob::class));
    }

    public function test_super_admin_can_view_specific_failed_job(): void
    {
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        $failedJob = $this->createFailedJob();

        $this->assertTrue($superAdmin->can('view', $failedJob));
    }

    public function test_regular_user_cannot_view_specific_failed_job(): void
    {
        $regularUser = User::factory()->create();
        $failedJob = $this->createFailedJob();

        $this->assertFalse($regularUser->can('view', $failedJob));
    }

    public function test_super_admin_can_delete_failed_job(): void
    {
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        $failedJob = $this->createFailedJob();

        $this->assertTrue($superAdmin->can('delete', $failedJob));
    }

    public function test_regular_user_cannot_delete_failed_job(): void
    {
        $regularUser = User::factory()->create();
        $failedJob = $this->createFailedJob();

        $this->assertFalse($regularUser->can('delete', $failedJob));
    }

    public function test_no_one_can_create_failed_jobs(): void
    {
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        $regularUser = User::factory()->create();

        $this->assertFalse($superAdmin->can('create', FailedJob::class));
        $this->assertFalse($regularUser->can('create', FailedJob::class));
    }

    public function test_no_one_can_edit_failed_jobs(): void
    {
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        $regularUser = User::factory()->create();
        $failedJob = $this->createFailedJob();

        $this->assertFalse($superAdmin->can('update', $failedJob));
        $this->assertFalse($regularUser->can('update', $failedJob));
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