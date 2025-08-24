<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class UploadTempo extends Model
{
    /** @use HasFactory<\Database\Factories\UploadTempoFactory> */
    use HasFactory;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<string, mixed>
     */
    protected $fillable = [
        'upload_id',
        'preset',
        'tempo_factor',
        'pitch_shift_semitones',
        'preserve_pitch',
        'add_reverb',
        'use_stems',
        'file_path',
        'public_path',
        'storage_type',
        'converted_to_ogg',
        'file_size',
        'duration',
        'final_bpm',
        'processing_metadata',
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
            'tempo_factor' => 'float',
            'pitch_shift_semitones' => 'float',
            'preserve_pitch' => 'boolean',
            'add_reverb' => 'boolean',
            'use_stems' => 'boolean',
            'converted_to_ogg' => 'boolean',
            'file_size' => 'integer',
            'duration' => 'float',
            'final_bpm' => 'float',
            'processing_metadata' => 'array',
        ];
    }

    /**
     * Get the upload that this tempo belongs to.
     */
    public function upload(): BelongsTo
    {
        return $this->belongsTo(Upload::class);
    }

    /**
     * Get the human-readable preset name.
     */
    public function getPresetName(): string
    {
        return match ($this->preset) {
            'sped_up' => 'Sped Up',
            'slowed_reverb' => 'Slowed + Reverb',
            'nightcore' => 'Nightcore',
            'chopped_screwed' => 'Chopped & Screwed',
            'custom' => 'Custom',
            default => ucwords(str_replace('_', ' ', $this->preset))
        };
    }

    /**
     * Get the file size in human-readable format.
     */
    public function getFormattedFileSize(): string
    {
        if (! $this->file_size) {
            return 'Unknown size';
        }

        $bytes = $this->file_size;
        $units = ['B', 'KB', 'MB', 'GB'];

        for ($i = 0; $bytes >= 1024 && $i < count($units) - 1; $i++) {
            $bytes /= 1024;
        }

        return round($bytes, 2).' '.$units[$i];
    }

    /**
     * Get the duration in human-readable format.
     */
    public function getFormattedDuration(): string
    {
        if (! $this->duration) {
            return 'Unknown duration';
        }

        $minutes = floor($this->duration / 60);
        $seconds = $this->duration % 60;

        return sprintf('%d:%02d', $minutes, $seconds);
    }

    /**
     * Get the tempo change description.
     */
    public function getTempoDescription(): string
    {
        if ($this->tempo_factor === 1.0) {
            return 'Original tempo';
        } elseif ($this->tempo_factor > 1.0) {
            $percentage = round(($this->tempo_factor - 1) * 100);

            return "{$percentage}% faster";
        } else {
            $percentage = round((1 - $this->tempo_factor) * 100);

            return "{$percentage}% slower";
        }
    }

    /**
     * Get the pitch change description.
     */
    public function getPitchDescription(): string
    {
        if (! $this->pitch_shift_semitones || $this->pitch_shift_semitones === 0.0) {
            return 'Original pitch';
        } elseif ($this->pitch_shift_semitones > 0) {
            return "+{$this->pitch_shift_semitones} semitones";
        } else {
            return "{$this->pitch_shift_semitones} semitones";
        }
    }

    /**
     * Check if the tempo file is stored locally.
     */
    public function isStoredLocally(): bool
    {
        return $this->storage_type === 'local';
    }

    /**
     * Check if the tempo file is stored on R2.
     */
    public function isStoredOnR2(): bool
    {
        return $this->storage_type === 'r2';
    }
}
