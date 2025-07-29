<?php

namespace Database\Seeders;

use App\Models\Contest;
use App\Models\ContestUser;
use App\Models\Upload;
use App\Models\User;
use App\Models\Vote;
// use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // Create admin user
        $adminUser = User::factory()->create([
            'name' => 'Admin User',
            'email' => 'admin@beatforge.com',
        ]);

        // Create test user
        $testUser = User::factory()->create([
            'name' => 'Test User',
            'email' => 'test@example.com',
        ]);

        // Create regular users
        $users = User::factory(10)->create();
        $allUsers = $users->merge([$adminUser, $testUser]);

        // Create uploads for each user
        $allUsers->each(function ($user) {
            Upload::factory(5)->for($user)->create();
        });

        // Create contests
        $contests = Contest::factory(5)
            ->for($adminUser)
            ->create([
                'state' => 'open',
                'start_date' => now()->subDays(10),
                'end_date' => now()->addDays(20),
            ]);

        // Add contest entries from users with their uploads
        $contests->each(function ($contest) use ($allUsers) {
            $participants = $allUsers->random(5);

            $participants->each(function ($user) use ($contest) {
                $upload = $user->uploads->random();

                ContestUser::factory()->create([
                    'user_id' => $user->id,
                    'contest_id' => $contest->id,
                    'upload_id' => $upload->id,
                    'title' => $upload->title,
                    'rating_at_contest' => $user->id * 100 + 1000, // Just to have a deterministic rating
                ]);
            });
        });
    }
}
