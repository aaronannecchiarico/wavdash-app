<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Spatie\Permission\Models\Role;
use Tests\TestCase;

class SuperAdminUploadListTest extends TestCase
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

    public function test_super_admin_sees_all_uploads_in_admin_panel(): void
    {
        // Create multiple users with uploads
        $user1 = User::factory()->create(['name' => 'User One']);
        $user2 = User::factory()->create(['name' => 'User Two']);

        $upload1 = Upload::factory()->create([
            'user_id' => $user1->id,
            'title' => 'Upload from User One',
        ]);

        $upload2 = Upload::factory()->create([
            'user_id' => $user2->id,
            'title' => 'Upload from User Two',
        ]);

        // Create SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should see both uploads in the admin list
        $response = $this->actingAs($superAdmin)
            ->get('/admin/uploads');

        $response->assertSuccessful();

        // The response should contain both uploads (checking the HTML content)
        $content = $response->getContent();
        $this->assertStringContainsString('Upload from User One', $content);
        $this->assertStringContainsString('Upload from User Two', $content);
    }

    public function test_super_admin_can_view_individual_uploads_from_different_users(): void
    {
        // Create a regular user and their upload
        $regularUser = User::factory()->create(['name' => 'Regular User']);
        $upload = Upload::factory()->create([
            'user_id' => $regularUser->id,
            'title' => 'Private Upload',
        ]);

        // Create SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should be able to view the specific upload
        $response = $this->actingAs($superAdmin)
            ->get("/admin/uploads/{$upload->id}");

        $response->assertSuccessful();

        // Should contain the upload details
        $content = $response->getContent();
        $this->assertStringContainsString('Private Upload', $content);
    }
}
