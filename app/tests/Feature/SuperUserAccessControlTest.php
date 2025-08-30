<?php

namespace Tests\Feature;

use App\Http\Middleware\EnsureSuperUser;
use App\Models\User;
use Filament\Panel;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use PHPUnit\Framework\Attributes\Test;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;
use Tests\TestCase;

class SuperUserAccessControlTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Reset cached roles and permissions
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();
    }

    #[Test]
    public function can_create_super_admin_role_and_permissions(): void
    {
        // Create permissions manually
        $adminPermissions = [
            'access admin panel',
            'manage users',
            'manage uploads',
            'manage contests',
            'view analytics',
            'manage system settings',
            'view system health',
            'manage roles and permissions',
        ];

        foreach ($adminPermissions as $permission) {
            Permission::create(['name' => $permission]);
        }

        // Create SuperAdmin role
        $superAdminRole = Role::create(['name' => 'SuperAdmin']);
        $superAdminRole->syncPermissions(Permission::all());

        // Verify all permissions were created
        $this->assertEquals(8, Permission::count());

        // Verify role has all permissions
        foreach ($adminPermissions as $permission) {
            $this->assertTrue($superAdminRole->hasPermissionTo($permission));
        }
    }

    #[Test]
    public function can_assign_super_admin_role_to_user(): void
    {
        // Create role and permissions
        $role = Role::create(['name' => 'SuperAdmin']);
        $permission = Permission::create(['name' => 'access admin panel']);
        $role->givePermissionTo($permission);

        // Create user
        $user = User::factory()->create([
            'name' => 'Super Administrator',
            'email' => 'admin@beatforge.com',
            'password' => Hash::make('secure-password'),
            'email_verified_at' => now(),
        ]);

        // Assign role
        $user->assignRole($role);

        // Verify
        $this->assertTrue($user->hasRole('SuperAdmin'));
        $this->assertTrue($user->hasPermissionTo('access admin panel'));
    }

    #[Test]
    public function ensure_super_user_middleware_redirects_unauthenticated_users(): void
    {
        $middleware = new EnsureSuperUser;
        $request = Request::create('/admin');

        $response = $middleware->handle($request, function () {
            return response('Should not reach here');
        });

        $this->assertEquals(302, $response->getStatusCode());
        $this->assertStringContainsString('/admin/login', $response->getTargetUrl());
    }

    #[Test]
    public function ensure_super_user_middleware_blocks_users_without_role(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        $middleware = new EnsureSuperUser;
        $request = Request::create('/admin');

        $this->expectException(\Symfony\Component\HttpKernel\Exception\NotFoundHttpException::class);

        $middleware->handle($request, function () {
            return response('Should not reach here');
        });
    }

    #[Test]
    public function ensure_super_user_middleware_allows_users_with_super_admin_role(): void
    {
        $user = User::factory()->create();
        $role = Role::create(['name' => 'SuperAdmin']);
        $user->assignRole($role);

        $this->actingAs($user);

        $middleware = new EnsureSuperUser;
        $request = Request::create('/admin');

        $response = $middleware->handle($request, function () {
            return response('Success');
        });

        $this->assertEquals('Success', $response->getContent());
    }

    #[Test]
    public function ensure_super_user_middleware_respects_config_role_name(): void
    {
        config(['admin.superuser_role' => 'CustomAdminRole']);

        $user = User::factory()->create();
        $role = Role::create(['name' => 'CustomAdminRole']);
        $user->assignRole($role);

        $this->actingAs($user);

        $middleware = new EnsureSuperUser;
        $request = Request::create('/admin');

        $response = $middleware->handle($request, function () {
            return response('Custom Role Success');
        });

        $this->assertEquals('Custom Role Success', $response->getContent());
    }

    #[Test]
    public function user_can_access_panel_method_works_correctly(): void
    {
        $user = User::factory()->create();
        $role = Role::create(['name' => 'SuperAdmin']);
        $user->assignRole($role);

        // Create a mock Filament panel
        $adminPanel = $this->createMock(Panel::class);
        $adminPanel->method('getId')->willReturn('admin');

        $otherPanel = $this->createMock(Panel::class);
        $otherPanel->method('getId')->willReturn('other');

        // User with SuperAdmin role can access admin panel
        $this->assertTrue($user->canAccessPanel($adminPanel));

        // User can access other panels regardless of role
        $this->assertTrue($user->canAccessPanel($otherPanel));

        // User without SuperAdmin role cannot access admin panel
        $user->removeRole($role);
        $this->assertFalse($user->canAccessPanel($adminPanel));
        $this->assertTrue($user->canAccessPanel($otherPanel));
    }

    #[Test]
    public function middleware_is_registered_in_bootstrap_app(): void
    {
        $aliases = app('router')->getMiddleware();

        $this->assertArrayHasKey('admin.superuser', $aliases);
        $this->assertEquals(EnsureSuperUser::class, $aliases['admin.superuser']);
    }

    #[Test]
    public function super_user_can_be_created_and_updated(): void
    {
        // Create initial user
        $user = User::create([
            'name' => 'Initial Name',
            'email' => 'admin@example.com',
            'password' => Hash::make('initial-password'),
            'email_verified_at' => now(),
        ]);

        // Create role and assign
        $role = Role::create(['name' => 'SuperAdmin']);
        $user->assignRole($role);

        $this->assertTrue($user->hasRole('SuperAdmin'));
        $this->assertEquals('Initial Name', $user->name);

        // Update user (simulating seeder update functionality)
        $user->update([
            'name' => 'Updated Name',
            'password' => Hash::make('new-password'),
        ]);

        $user->refresh();
        $this->assertEquals('Updated Name', $user->name);
        $this->assertTrue(Hash::check('new-password', $user->password));
        $this->assertTrue($user->hasRole('SuperAdmin'));
    }

    #[Test]
    public function config_admin_superuser_role_is_respected(): void
    {
        config(['admin.superuser_role' => 'CustomSuperRole']);

        $user = User::factory()->create();
        $role = Role::create(['name' => 'CustomSuperRole']);
        $permission = Permission::create(['name' => 'access admin panel']);
        $role->givePermissionTo($permission);
        $user->assignRole($role);

        // Test middleware uses config value
        $this->actingAs($user);
        $middleware = new EnsureSuperUser;
        $request = Request::create('/admin');

        $response = $middleware->handle($request, function () {
            return response('Config Role Works');
        });

        $this->assertEquals('Config Role Works', $response->getContent());
    }

    #[Test]
    public function complete_integration_test(): void
    {
        // This test simulates the complete integration setup

        // 1. Create all admin permissions
        $adminPermissions = [
            'access admin panel',
            'manage users',
            'manage uploads',
            'manage contests',
            'view analytics',
            'manage system settings',
            'view system health',
            'manage roles and permissions',
        ];

        foreach ($adminPermissions as $permission) {
            Permission::create(['name' => $permission]);
        }

        // 2. Create SuperAdmin role with all permissions
        $superAdminRole = Role::create(['name' => config('admin.superuser_role', 'SuperAdmin')]);
        $superAdminRole->syncPermissions(Permission::all());

        // 3. Create SuperUser with role
        $superUser = User::create([
            'name' => 'Super Administrator',
            'email' => 'admin@beatforge.com',
            'password' => Hash::make('SecureAdminPassword123!'),
            'email_verified_at' => now(),
        ]);
        $superUser->assignRole($superAdminRole);

        // 4. Test authentication flow
        $this->actingAs($superUser);

        // 5. Test middleware allows access
        $middleware = new EnsureSuperUser;
        $request = Request::create('/admin');

        $response = $middleware->handle($request, function () {
            return response('Admin Access Granted');
        });

        $this->assertEquals('Admin Access Granted', $response->getContent());

        // 6. Test canAccessPanel method
        $adminPanel = $this->createMock(Panel::class);
        $adminPanel->method('getId')->willReturn('admin');

        $this->assertTrue($superUser->canAccessPanel($adminPanel));

        // 7. Verify user has all expected permissions
        foreach ($adminPermissions as $permission) {
            $this->assertTrue($superUser->hasPermissionTo($permission));
        }
    }
}