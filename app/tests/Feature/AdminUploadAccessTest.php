<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Spatie\Permission\Models\Role;
use Tests\TestCase;

class AdminUploadAccessTest extends TestCase
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

    public function test_super_admin_can_access_upload_list_in_admin_panel(): void
    {
        // Create a SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // Create some uploads from different users
        $regularUser = User::factory()->create();
        Upload::factory()->create(['user_id' => $regularUser->id]);
        Upload::factory()->create(['user_id' => $superAdmin->id]);

        // SuperAdmin should be able to access the uploads list
        $response = $this->actingAs($superAdmin)
            ->get('/admin/uploads');

        $response->assertSuccessful();
    }

    public function test_super_admin_can_view_specific_upload_in_admin_panel(): void
    {
        // Create a regular user and their upload
        $regularUser = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // Create a SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should be able to view the specific upload
        $response = $this->actingAs($superAdmin)
            ->get("/admin/uploads/{$upload->id}");

        $response->assertSuccessful();
    }

    public function test_super_admin_can_access_upload_edit_page(): void
    {
        // Create a regular user and their upload
        $regularUser = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // Create a SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should be able to access the edit page
        $response = $this->actingAs($superAdmin)
            ->get("/admin/uploads/{$upload->id}/edit");

        $response->assertSuccessful();
    }

    public function test_regular_user_cannot_access_admin_panel_uploads(): void
    {
        // Create a regular user and their upload
        $regularUser = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // Regular user should not be able to access admin panel uploads
        $response = $this->actingAs($regularUser)
            ->get('/admin/uploads');

        // Should be blocked by the admin middleware (redirect or 403)
        $this->assertContains($response->getStatusCode(), [302, 403, 404]);
    }
}