<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\Support\OptimizedTestTrait;
use Tests\TestCase;

class AdminUploadAccessTest extends TestCase
{
    use OptimizedTestTrait, RefreshDatabase;

    public function test_super_admin_can_access_upload_list_in_admin_panel(): void
    {
        // Use optimized reusable super admin
        $superAdmin = $this->getTestSuperAdmin();
        $regularUser = $this->getTestUser();

        // Create some uploads using the for() method to ensure proper relationships
        Upload::factory()->for($regularUser)->create();
        Upload::factory()->for($superAdmin)->create();

        // SuperAdmin should be able to access the uploads list
        $response = $this->actingAs($superAdmin)
            ->get('/admin/uploads');

        $response->assertSuccessful();
    }

    public function test_super_admin_can_view_specific_upload_in_admin_panel(): void
    {
        // Use optimized reusable users
        $regularUser = $this->getTestUser();
        $superAdmin = $this->getTestSuperAdmin();

        // Create upload explicitly with the user ID
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // SuperAdmin should be able to view the specific upload
        $response = $this->actingAs($superAdmin)
            ->get("/admin/uploads/{$upload->id}");

        $response->assertSuccessful();
    }

    public function test_super_admin_can_access_upload_edit_page(): void
    {
        // Use optimized reusable users
        $regularUser = $this->getTestUser();
        $superAdmin = $this->getTestSuperAdmin();

        // Create upload explicitly with the user ID
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // SuperAdmin should be able to access the edit page
        $response = $this->actingAs($superAdmin)
            ->get("/admin/uploads/{$upload->id}/edit");

        $response->assertSuccessful();
    }

    public function test_regular_user_cannot_access_admin_panel_uploads(): void
    {
        // Use optimized reusable user
        $regularUser = $this->getTestUser();
        Upload::factory()->create(['user_id' => $regularUser->id]);

        // Regular user should not be able to access admin panel uploads
        $response = $this->actingAs($regularUser)
            ->get('/admin/uploads');

        // Should be blocked by the admin middleware (redirect or 403)
        $this->assertContains($response->getStatusCode(), [302, 403, 404]);
    }
}
