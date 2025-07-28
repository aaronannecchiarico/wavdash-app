<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;
use App\Models\;
use App\Models\ContestUser;
use App\Models\User;

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
        return [
            'user_id' => User::factory(),
            'contest_id' => ::factory(),
            'title' => fake()->sentence(4),
            'rating_at_contest' => fake()->numberBetween(-10000, 10000),
            'original_path' => fake()->word(),
            'status' => fake()->randomElement(["pending","processing","ready","failed"]),
        ];
    }
}
