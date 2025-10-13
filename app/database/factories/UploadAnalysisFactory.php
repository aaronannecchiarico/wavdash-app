<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\UploadAnalysis>
 */
class UploadAnalysisFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
        $modes = ['major', 'minor'];

        return [
            'musical_key' => fake()->randomElement($keys).' '.fake()->randomElement($modes),
            'key_confidence' => fake()->randomFloat(2, 0.5, 1.0),
            'bpm' => fake()->numberBetween(60, 180),
            'beat_regularity' => fake()->randomFloat(2, 0.5, 1.0),
            'loudness_db' => fake()->randomFloat(2, -40, -5),
            'dynamic_range_db' => fake()->randomFloat(2, 5, 20),
            'brightness' => fake()->randomFloat(2, 0, 1),
            'timbral_complexity' => fake()->randomFloat(2, 0, 1),
            'analysis_duration' => fake()->randomFloat(2, 1, 60),
            'chunk_count' => fake()->numberBetween(10, 100),
            'key_changes' => fake()->numberBetween(0, 5),
        ];
    }
}
