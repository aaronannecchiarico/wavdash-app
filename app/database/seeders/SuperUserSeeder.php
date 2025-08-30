<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;
use Spatie\Permission\PermissionRegistrar;

class SuperUserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Reset cached roles and permissions
        app()[PermissionRegistrar::class]->forgetCachedPermissions();

        $this->command->info('Creating admin permissions...');

        // Create admin permissions
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
            Permission::firstOrCreate(['name' => $permission]);
            $this->command->info("✓ Permission '{$permission}' created");
        }

        $this->command->info('Creating SuperAdmin role...');

        // Create SuperAdmin role
        $superAdminRole = Role::firstOrCreate(['name' => config('admin.superuser_role', 'SuperAdmin')]);

        // Give all permissions to SuperAdmin
        $superAdminRole->syncPermissions(Permission::all());
        $this->command->info('✓ SuperAdmin role created with all permissions');

        $this->command->info('Creating SuperUser account...');

        // Get SuperUser credentials from environment
        $name = env('SUPER_USER_NAME', 'Super Administrator');
        $email = env('SUPER_USER_EMAIL', 'admin@beatforge.com');
        $password = env('SUPER_USER_PASSWORD');

        // Validate required environment variables
        if (! $password) {
            $this->command->error('SUPER_USER_PASSWORD environment variable is required');
            $this->command->warn('Please set SUPER_USER_PASSWORD in your .env file');

            return;
        }

        if (! filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $this->command->error('Invalid email address in SUPER_USER_EMAIL');

            return;
        }

        // Create SuperUser
        $superUser = User::firstOrCreate(
            ['email' => $email],
            [
                'name' => $name,
                'password' => Hash::make($password),
                'email_verified_at' => now(),
            ]
        );

        // Update password if user already exists (in case it changed)
        if (! $superUser->wasRecentlyCreated) {
            $superUser->update([
                'name' => $name,
                'password' => Hash::make($password),
            ]);
            $this->command->info('✓ SuperUser account updated');
        } else {
            $this->command->info('✓ SuperUser account created');
        }

        // Assign SuperAdmin role
        $superUser->assignRole($superAdminRole);

        $this->command->newLine();
        $this->command->info('SuperUser setup completed successfully!');
        $this->command->info('Email: '.$superUser->email);
        $this->command->info('Role: '.config('admin.superuser_role', 'SuperAdmin'));
        $this->command->newLine();
        $this->command->warn('IMPORTANT: Please change the default password after first login!');
        $this->command->warn('IMPORTANT: Ensure SUPER_USER_PASSWORD is removed from production .env files!');
    }
}
