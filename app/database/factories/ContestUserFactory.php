<?php

namespace Database\Factories;

use App\Models\Contest;
use App\Models\ContestUser;
use App\Models\Upload;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

class ContestUserFactory extends Factory
{
    /**
     * The name of the factory's corresponding model.
     *
     * @var string
     */
    protected $model = ContestUser::class;

    /**
     * Define the model's default state.
     */
    public function definition(): array
    {
        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'status' => 'ready',
        ]);

        return [
            'user_id' => $user->id,
            'contest_id' => Contest::factory(),
            'upload_id' => $upload->id,
            'title' => $upload->title, // Default to the upload's title, can be overridden
            'rating_at_contest' => fake()->numberBetween(800, 1600),
            'original_path' => null, // Path now comes from the upload
            'status' => 'ready',
        ];
    }
}
