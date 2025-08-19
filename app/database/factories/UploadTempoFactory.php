<?php

namespace Database\Factories;

use App\Models\Upload;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\UploadTempo>
 */
class UploadTempoFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $presets = ['sped_up', 'slowed_reverb', 'nightcore', 'chopped_screwed', 'custom'];
        $preset = $this->faker->randomElement($presets);

        // Generate tempo factor based on preset
        $tempoFactor = match ($preset) {
            'sped_up' => $this->faker->randomFloat(2, 1.1, 1.5),
            'slowed_reverb' => $this->faker->randomFloat(2, 0.6, 0.9),
            'nightcore' => $this->faker->randomFloat(2, 1.2, 1.6),
            'chopped_screwed' => $this->faker->randomFloat(2, 0.5, 0.8),
            default => $this->faker->randomFloat(2, 0.5, 2.0),
        };

        return [
            'upload_id' => Upload::factory(),
            'preset' => $preset,
            'tempo_factor' => $tempoFactor,
            'pitch_shift_semitones' => $this->faker->randomFloat(1, -6, 6),
            'preserve_pitch' => $this->faker->boolean(30), // 30% chance
            'add_reverb' => $preset === 'slowed_reverb' ? true : $this->faker->boolean(20),
            'use_stems' => $this->faker->boolean(10), // 10% chance
            'file_path' => 'private/processed/'.$this->faker->numberBetween(1, 100).'/'.
                         $this->faker->date('Y/m/d').'/'.
                         $this->faker->word().'_tempo_'.$preset.'.wav',
            'storage_type' => $this->faker->randomElement(['local', 'r2']),
            'file_size' => $this->faker->numberBetween(1000000, 50000000), // 1MB to 50MB
            'duration' => $this->faker->randomFloat(1, 30, 600), // 30 seconds to 10 minutes
            'final_bpm' => $this->faker->numberBetween(60, 200),
            'processing_metadata' => [
                'processing_time' => $this->faker->randomFloat(2, 5, 120),
                'quality_score' => $this->faker->randomFloat(2, 0.7, 1.0),
                'effects_applied' => ['tempo_change'],
                'processing_warnings' => [],
            ],
        ];
    }

    /**
     * Indicate that the tempo is for a nightcore preset.
     */
    public function nightcore(): static
    {
        return $this->state(fn (array $attributes) => [
            'preset' => 'nightcore',
            'tempo_factor' => $this->faker->randomFloat(2, 1.2, 1.6),
            'pitch_shift_semitones' => $this->faker->randomFloat(1, 2, 6),
            'preserve_pitch' => false,
        ]);
    }

    /**
     * Indicate that the tempo is for a slowed + reverb preset.
     */
    public function slowedReverb(): static
    {
        return $this->state(fn (array $attributes) => [
            'preset' => 'slowed_reverb',
            'tempo_factor' => $this->faker->randomFloat(2, 0.6, 0.9),
            'pitch_shift_semitones' => $this->faker->randomFloat(1, -4, 0),
            'preserve_pitch' => false,
            'add_reverb' => true,
        ]);
    }

    /**
     * Indicate that the tempo file is stored locally.
     */
    public function local(): static
    {
        return $this->state(fn (array $attributes) => [
            'storage_type' => 'local',
            'file_path' => 'private/'.trim($attributes['file_path'] ?? '', 'private/'),
        ]);
    }

    /**
     * Indicate that the tempo file is stored on R2.
     */
    public function r2(): static
    {
        return $this->state(fn (array $attributes) => [
            'storage_type' => 'r2',
        ]);
    }

    /**
     * Indicate that the tempo has no file size (unknown).
     */
    public function unknownSize(): static
    {
        return $this->state(fn (array $attributes) => [
            'file_size' => null,
        ]);
    }

    /**
     * Indicate that the tempo has no duration (unknown).
     */
    public function unknownDuration(): static
    {
        return $this->state(fn (array $attributes) => [
            'duration' => null,
        ]);
    }
}
