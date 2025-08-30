<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\Test;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;
use Tests\TestCase;

class SuperUserAdminAccessTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Reset cached roles and permissions
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();
    }

    #[Test]
    public function user_model_has_roles_trait(): void
    {
        $user = User::factory()->create();

        // Test that the User model uses HasRoles trait
        $this->assertTrue(method_exists($user, 'assignRole'));
        $this->assertTrue(method_exists($user, 'hasRole'));
        $this->assertTrue(method_exists($user, 'hasPermissionTo'));
    }

    #[Test]
    public function can_create_super_admin_role(): void
    {
        $role = Role::create(['name' => 'SuperAdmin']);

        $this->assertDatabaseHas('roles', ['name' => 'SuperAdmin']);
        $this->assertEquals('SuperAdmin', $role->name);
    }

    #[Test]
    public function can_create_admin_permissions(): void
    {
        $permissions = [
            'access admin panel',
            'manage users',
            'manage uploads',
            'manage contests',
            'view analytics',
            'manage system settings',
            'view system health',
            'manage roles and permissions',
        ];

        foreach ($permissions as $permission) {
            $created = Permission::create(['name' => $permission]);
            $this->assertDatabaseHas('permissions', ['name' => $permission]);
            $this->assertEquals($permission, $created->name);
        }
    }

    #[Test]
    public function can_assign_super_admin_role_to_user(): void
    {
        $user = User::factory()->create();
        $role = Role::create(['name' => 'SuperAdmin']);

        $user->assignRole($role);

        $this->assertTrue($user->hasRole('SuperAdmin'));
        $this->assertDatabaseHas('model_has_roles', [
            'role_id' => $role->id,
            'model_id' => $user->id,
            'model_type' => User::class,
        ]);
    }

    #[Test]
    public function super_admin_role_can_have_permissions(): void
    {
        $role = Role::create(['name' => 'SuperAdmin']);
        $permission = Permission::create(['name' => 'access admin panel']);

        $role->givePermissionTo($permission);

        $this->assertTrue($role->hasPermissionTo('access admin panel'));
        $this->assertDatabaseHas('role_has_permissions', [
            'role_id' => $role->id,
            'permission_id' => $permission->id,
        ]);
    }

    #[Test]
    public function user_with_super_admin_role_has_permissions(): void
    {
        $user = User::factory()->create();
        $role = Role::create(['name' => 'SuperAdmin']);
        $permission = Permission::create(['name' => 'access admin panel']);

        $role->givePermissionTo($permission);
        $user->assignRole($role);

        $this->assertTrue($user->hasPermissionTo('access admin panel'));
        $this->assertTrue($user->hasRole('SuperAdmin'));
    }

    #[Test]
    public function admin_config_file_exists_and_has_correct_structure(): void
    {
        $config = config('admin');

        $this->assertIsArray($config);
        $this->assertArrayHasKey('enabled', $config);
        $this->assertArrayHasKey('ip_whitelist', $config);
        $this->assertArrayHasKey('superuser_role', $config);
        $this->assertArrayHasKey('session_name', $config);
        $this->assertArrayHasKey('session_lifetime', $config);
        $this->assertArrayHasKey('rate_limiting', $config);
    }

    #[Test]
    public function admin_config_has_correct_default_values(): void
    {
        $config = config('admin');

        $this->assertTrue($config['enabled']);
        $this->assertEquals('SuperAdmin', $config['superuser_role']);
        $this->assertEquals('admin_session', $config['session_name']);
        $this->assertEquals(120, $config['session_lifetime']);

        // IP whitelist structure
        $this->assertArrayHasKey('enabled', $config['ip_whitelist']);
        $this->assertArrayHasKey('allowed_ips', $config['ip_whitelist']);
        $this->assertArrayHasKey('return_404_on_reject', $config['ip_whitelist']);

        // Rate limiting structure
        $this->assertArrayHasKey('login_attempts', $config['rate_limiting']);
        $this->assertArrayHasKey('global_requests', $config['rate_limiting']);
    }

    #[Test]
    public function admin_config_respects_environment_variables(): void
    {
        // Test with custom config values
        config(['admin.enabled' => false]);
        config(['admin.superuser_role' => 'CustomAdmin']);
        config(['admin.session_lifetime' => 60]);

        $this->assertFalse(config('admin.enabled'));
        $this->assertEquals('CustomAdmin', config('admin.superuser_role'));
        $this->assertEquals(60, config('admin.session_lifetime'));
    }

    #[Test]
    public function permission_tables_exist_in_database(): void
    {
        // Check if all Spatie permission tables exist
        $this->assertTrue(\Schema::hasTable('permissions'));
        $this->assertTrue(\Schema::hasTable('roles'));
        $this->assertTrue(\Schema::hasTable('model_has_permissions'));
        $this->assertTrue(\Schema::hasTable('model_has_roles'));
        $this->assertTrue(\Schema::hasTable('role_has_permissions'));
    }

    #[Test]
    public function can_clear_and_reset_permissions_cache(): void
    {
        // Create a role and permission
        $role = Role::create(['name' => 'TestRole']);
        $permission = Permission::create(['name' => 'test permission']);
        $role->givePermissionTo($permission);

        // Reset cached permissions
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();

        // Verify permissions still work after cache reset
        $this->assertTrue($role->fresh()->hasPermissionTo('test permission'));
    }

    #[Test]
    public function multiple_roles_can_be_created_and_managed(): void
    {
        $roles = ['SuperAdmin', 'Admin', 'Moderator', 'User'];

        foreach ($roles as $roleName) {
            $role = Role::create(['name' => $roleName]);
            $this->assertDatabaseHas('roles', ['name' => $roleName]);
        }

        $this->assertEquals(4, Role::count());
    }

    #[Test]
    public function user_can_have_multiple_roles(): void
    {
        $user = User::factory()->create();
        $adminRole = Role::create(['name' => 'Admin']);
        $moderatorRole = Role::create(['name' => 'Moderator']);

        $user->assignRole([$adminRole, $moderatorRole]);

        $this->assertTrue($user->hasRole('Admin'));
        $this->assertTrue($user->hasRole('Moderator'));
        $this->assertTrue($user->hasAnyRole(['Admin', 'Moderator']));
    }

    #[Test]
    public function permissions_can_be_assigned_directly_to_user(): void
    {
        $user = User::factory()->create();
        $permission = Permission::create(['name' => 'direct permission']);

        $user->givePermissionTo($permission);

        $this->assertTrue($user->hasPermissionTo('direct permission'));
        $this->assertDatabaseHas('model_has_permissions', [
            'permission_id' => $permission->id,
            'model_id' => $user->id,
            'model_type' => User::class,
        ]);
    }
}
