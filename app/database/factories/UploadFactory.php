<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Upload>
 */
class UploadFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'user_id' => \App\Models\User::factory(),
            'title' => $this->faker->words(3, true),
            'description' => $this->faker->optional()->paragraph(),
            'genre' => $this->faker->randomElement(['Hip Hop', 'Electronic', 'Pop', 'Rock', 'Jazz', 'Classical', 'Lo-Fi']),
            'original_path' => 's3://beatforge/' . $this->faker->uuid . '.mp3',
            'web_path' => $this->faker->optional()->url(),
            'status' => $this->faker->randomElement(['pending', 'processing', 'ready', 'failed']),
            'duration_seconds' => $this->faker->numberBetween(60, 600),
        ];
    }
}
