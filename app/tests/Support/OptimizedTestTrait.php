<?php

declare(strict_types=1);

namespace Tests\Support;

use App\Models\User;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Spatie\Permission\Models\Role;

trait OptimizedTestTrait
{
    private static array $testClassUsers = [];
    private static array $testClassSuperAdmins = [];
    private static array $testClassSuperAdminRoles = [];

    /**
     * Get or create a reusable test user for this test class
     */
    protected function getTestUser(): User
    {
        $testClass = static::class;
        
        // Check if cached user still exists in database
        if (isset(static::$testClassUsers[$testClass])) {
            $cachedUser = static::$testClassUsers[$testClass];
            if (User::find($cachedUser->id)) {
                return $cachedUser;
            }
            // Clear cache if user no longer exists
            unset(static::$testClassUsers[$testClass]);
        }

        static::$testClassUsers[$testClass] = User::factory()->create();
        return static::$testClassUsers[$testClass];
    }

    /**
     * Get or create a reusable super admin user for this test class
     */
    protected function getTestSuperAdmin(): User
    {
        $testClass = static::class;
        
        // Check if cached super admin still exists in database
        if (isset(static::$testClassSuperAdmins[$testClass])) {
            $cachedSuperAdmin = static::$testClassSuperAdmins[$testClass];
            if (User::find($cachedSuperAdmin->id)) {
                return $cachedSuperAdmin;
            }
            // Clear cache if user no longer exists
            unset(static::$testClassSuperAdmins[$testClass]);
        }

        static::$testClassSuperAdmins[$testClass] = User::factory()->create();
        static::$testClassSuperAdmins[$testClass]->assignRole($this->getSuperAdminRole());
        return static::$testClassSuperAdmins[$testClass];
    }

    /**
     * Get or create the SuperAdmin role for this test class
     */
    protected function getSuperAdminRole(): Role
    {
        $testClass = static::class;
        
        // Check if cached role still exists in database
        if (isset(static::$testClassSuperAdminRoles[$testClass])) {
            $cachedRole = static::$testClassSuperAdminRoles[$testClass];
            if (Role::find($cachedRole->id)) {
                return $cachedRole;
            }
            // Clear cache if role no longer exists
            unset(static::$testClassSuperAdminRoles[$testClass]);
        }

        // Reset cached roles and permissions
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();
        
        static::$testClassSuperAdminRoles[$testClass] = Role::firstOrCreate(['name' => 'SuperAdmin']);
        return static::$testClassSuperAdminRoles[$testClass];
    }

    /**
     * Set up common HTTP mocks for audio microservice tests
     */
    protected function setupAudioMicroserviceMocks(array $additionalFakes = []): void
    {
        $defaultFakes = [
            '*' => Http::response(['status' => 'healthy'], 200),
            'http://localhost:8001/storage/status' => Http::response([
                'enabled' => true,
                'storage_type' => 'r2',
                'message' => 'R2 storage is enabled and ready',
            ], 200),
        ];

        Http::fake(array_merge($defaultFakes, $additionalFakes));
    }

    /**
     * Set up common storage fakes for performance
     */
    protected function setupStorageFakes(): void
    {
        Storage::fake('r2');
        Storage::fake('r2_private');
        Storage::fake('r2_public');
        Storage::fake('r2_stream');
        Storage::fake('private');
        Storage::fake('public');
    }

    /**
     * Set up FFMpeg mocks to avoid actual audio processing
     */
    protected function setupFFMpegMocks(): void
    {
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('fromDisk')
            ->andReturnSelf();
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('fromFilesystem')
            ->andReturnSelf();
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('open')
            ->andReturnSelf();
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('getDurationInSeconds')
            ->andReturn(180.5);
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('export')
            ->andReturnSelf();
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('toDisk')
            ->andReturnSelf();
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('inFormat')
            ->andReturnSelf();
        \ProtoneMedia\LaravelFFMpeg\Support\FFMpeg::shouldReceive('save')
            ->andReturnUsing(function ($filename) {
                // Create a temporary file with the expected name
                $tempPath = sys_get_temp_dir() . '/' . $filename;
                file_put_contents($tempPath, 'fake ogg content');
                return true;
            });
    }

    /**
     * Clean up temporary files created during testing
     */
    protected function cleanupTempFiles(array $files): void
    {
        foreach ($files as $file) {
            if (file_exists($file)) {
                unlink($file);
            }
        }
    }
}