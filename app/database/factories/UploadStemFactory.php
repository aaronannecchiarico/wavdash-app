<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\UploadStem>
 */
class UploadStemFactory extends Factory
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
            'stem_type' => fake()->randomElement(['vocals', 'drums', 'bass', 'other']),
            'file_path' => fake()->filePath(),
            'storage_type' => fake()->randomElement(['local', 'r2']),
            'file_size' => fake()->numberBetween(1000000, 50000000), // 1MB to 50MB
            'duration' => fake()->randomFloat(2, 30, 600), // 30 seconds to 10 minutes
            'metadata' => [
                'processing_time' => fake()->randomFloat(2, 1, 30),
                'model_used' => 'htdemucs',
            ],
        ];
    }
}
