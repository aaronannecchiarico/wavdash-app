<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\UploadTempoTask>
 */
class UploadTempoTaskFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'task_id' => fake()->uuid(),
            'status' => fake()->randomElement(['pending', 'processing', 'completed', 'failed']),
            'progress' => fake()->numberBetween(0, 100),
            'processing_options' => json_encode([
                'presets' => ['sped_up', 'slowed_reverb'],
            ]),
            'submitted_at' => now(),
        ];
    }
}
