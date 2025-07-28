<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;
use App\Models\User;
use App\Models\UserMetadata;

class UserMetadataFactory extends Factory
{
    /**
     * The name of the factory's corresponding model.
     *
     * @var string
     */
    protected $model = UserMetadata::class;

    /**
     * Define the model's default state.
     */
    public function definition(): array
    {
        return [
            'user_id' => User::factory(),
            'wins' => fake()->numberBetween(-10000, 10000),
            'losses' => fake()->numberBetween(-10000, 10000),
            'elo_rating' => fake()->numberBetween(-10000, 10000),
        ];
    }
}
