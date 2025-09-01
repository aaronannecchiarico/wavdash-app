<?php

namespace Tests\Feature;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Spatie\Permission\Models\Role;
use Tests\TestCase;

class UploadPolicyTest extends TestCase
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

    public function test_super_admin_can_view_any_upload(): void
    {
        // Create a regular user and their upload
        $regularUser = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // Create a SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should be able to view any upload
        $this->assertTrue($superAdmin->can('view', $upload));
    }

    public function test_regular_user_can_only_view_own_uploads(): void
    {
        // Create two regular users
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        
        // Create uploads for each user
        $upload1 = Upload::factory()->create(['user_id' => $user1->id]);
        $upload2 = Upload::factory()->create(['user_id' => $user2->id]);

        // User1 can view their own upload
        $this->assertTrue($user1->can('view', $upload1));
        
        // User1 cannot view User2's upload
        $this->assertFalse($user1->can('view', $upload2));
        
        // User2 can view their own upload
        $this->assertTrue($user2->can('view', $upload2));
        
        // User2 cannot view User1's upload
        $this->assertFalse($user2->can('view', $upload1));
    }

    public function test_super_admin_can_view_any_uploads_list(): void
    {
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should be able to view any uploads
        $this->assertTrue($superAdmin->can('viewAny', Upload::class));
    }

    public function test_regular_user_can_view_uploads_list(): void
    {
        $regularUser = User::factory()->create();

        // Regular users can view the uploads list (but will be filtered by policy)
        $this->assertTrue($regularUser->can('viewAny', Upload::class));
    }

    public function test_super_admin_can_update_any_upload(): void
    {
        // Create a regular user and their upload
        $regularUser = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // Create a SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should be able to update any upload
        $this->assertTrue($superAdmin->can('update', $upload));
    }

    public function test_super_admin_can_delete_any_upload(): void
    {
        // Create a regular user and their upload
        $regularUser = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $regularUser->id]);

        // Create a SuperAdmin user
        $superAdmin = User::factory()->create();
        $superAdmin->assignRole('SuperAdmin');

        // SuperAdmin should be able to delete any upload
        $this->assertTrue($superAdmin->can('delete', $upload));
    }

    public function test_regular_user_cannot_update_others_uploads(): void
    {
        // Create two regular users
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        
        $upload1 = Upload::factory()->create(['user_id' => $user1->id]);
        $upload2 = Upload::factory()->create(['user_id' => $user2->id]);

        // User1 cannot update User2's upload
        $this->assertFalse($user1->can('update', $upload2));
        
        // User2 cannot update User1's upload
        $this->assertFalse($user2->can('update', $upload1));
    }

    public function test_regular_user_cannot_delete_others_uploads(): void
    {
        // Create two regular users
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();
        
        $upload1 = Upload::factory()->create(['user_id' => $user1->id]);
        $upload2 = Upload::factory()->create(['user_id' => $user2->id]);

        // User1 cannot delete User2's upload
        $this->assertFalse($user1->can('delete', $upload2));
        
        // User2 cannot delete User1's upload
        $this->assertFalse($user2->can('delete', $upload1));
    }
}