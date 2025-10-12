<?php

namespace Tests\Support;

use App\Models\User;
use Spatie\Permission\Models\Role;

trait OptimizedDatabaseTrait
{
    protected static bool $databaseSeeded = false;

    protected function seedTestDatabase(): void
    {
        if (! static::$databaseSeeded) {
            // Create common test users that can be reused
            User::factory()->count(5)->create();

            // Create common roles
            Role::firstOrCreate(['name' => 'SuperAdmin']);
            Role::firstOrCreate(['name' => 'User']);

            static::$databaseSeeded = true;
        }
    }

    /**
     * Override setUp to seed the database once per test class
     */
    protected function setUp(): void
    {
        parent::setUp();
        $this->seedTestDatabase();
    }

    /**
     * Get a reusable test user by index (1-5)
     */
    protected function getTestUserByIndex(int $index = 1): User
    {
        $this->seedTestDatabase();

        return User::find($index) ?? User::factory()->create();
    }

    /**
     * Get a reusable super admin user
     */
    protected function getTestSuperAdminUser(): User
    {
        $this->seedTestDatabase();
        $superAdmin = User::find(5); // Use the 5th user as super admin
        if (! $superAdmin) {
            $superAdmin = User::factory()->create();
        }

        $role = Role::firstOrCreate(['name' => 'SuperAdmin']);
        if (! $superAdmin->hasRole('SuperAdmin')) {
            $superAdmin->assignRole($role);
        }

        return $superAdmin;
    }
}
