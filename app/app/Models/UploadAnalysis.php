<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class UploadAnalysis extends Model
{
    use HasFactory;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<string, mixed>
     */
    protected $fillable = [
        'upload_id',
        'musical_key',
        'key_confidence',
        'bpm',
        'beat_regularity',
        'loudness_db',
        'dynamic_range_db',
        'brightness',
        'timbral_complexity',
        'analysis_duration',
        'chunk_count',
        'key_changes',
    ];

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'id' => 'integer',
            'upload_id' => 'integer',
            'key_confidence' => 'float',
            'bpm' => 'integer',
            'beat_regularity' => 'float',
            'loudness_db' => 'float',
            'dynamic_range_db' => 'float',
            'brightness' => 'float',
            'timbral_complexity' => 'float',
            'analysis_duration' => 'float',
            'chunk_count' => 'integer',
            'key_changes' => 'integer',
        ];
    }

    /**
     * Get the upload that this analysis belongs to.
     */
    public function upload(): BelongsTo
    {
        return $this->belongsTo(Upload::class);
    }

    /**
     * Get the BPM category based on the detected BPM.
     */
    public function getBpmCategory(): ?string
    {
        if (! $this->bpm) {
            return null;
        }

        return match (true) {
            $this->bpm >= 140 => 'Fast',
            $this->bpm >= 120 => 'Upbeat',
            $this->bpm >= 90 => 'Moderate',
            default => 'Slow'
        };
    }

    /**
     * Get the loudness category based on dB level.
     */
    public function getLoudnessCategory(): ?string
    {
        if (! $this->loudness_db) {
            return null;
        }

        return match (true) {
            $this->loudness_db >= -6 => 'Very Loud',
            $this->loudness_db >= -12 => 'Loud',
            $this->loudness_db >= -18 => 'Moderate',
            default => 'Quiet'
        };
    }

    /**
     * Get the dynamic range category.
     */
    public function getDynamicRangeCategory(): ?string
    {
        if (! $this->dynamic_range_db) {
            return null;
        }

        return match (true) {
            $this->dynamic_range_db > 20 => 'High Range',
            $this->dynamic_range_db >= 10 => 'Moderate',
            default => 'Compressed'
        };
    }

    /**
     * Get the brightness category based on spectral centroid.
     */
    public function getBrightnessCategory(): ?string
    {
        if (! $this->brightness) {
            return null;
        }

        return match (true) {
            $this->brightness > 2000 => 'Bright',
            $this->brightness >= 1000 => 'Balanced',
            default => 'Dark/Warm'
        };
    }

    /**
     * Check if key detection is reliable.
     */
    public function hasReliableKey(): bool
    {
        return $this->key_confidence && $this->key_confidence > 0.8;
    }

    /**
     * Check if key detection shows atonal/complex music.
     */
    public function isAtonalComplex(): bool
    {
        return $this->key_confidence && $this->key_confidence < 0.6;
    }
}
