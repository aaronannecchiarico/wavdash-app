<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\UploadStemTask>
 */
class UploadStemTaskFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'upload_id' => \App\Models\Upload::factory(),
            'task_id' => fake()->uuid(),
            'status' => fake()->randomElement(['pending', 'processing', 'completed', 'failed', 'deleted']),
            'progress' => fake()->numberBetween(0, 100),
            'submitted_at' => fake()->dateTimeThisMonth(),
            'completed_at' => fake()->optional()->dateTimeThisMonth(),
            'error_message' => fake()->optional()->sentence(),
        ];
    }
}
