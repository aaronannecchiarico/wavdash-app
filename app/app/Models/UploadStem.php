<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class UploadStem extends Model
{
    /** @use HasFactory<\Database\Factories\UploadStemFactory> */
    use HasFactory;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<string, mixed>
     */
    protected $fillable = [
        'upload_id',
        'stem_type',
        'file_path',
        'public_path',
        'storage_type',
        'converted_to_ogg',
        'file_size',
        'duration',
        'metadata',
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
            'converted_to_ogg' => 'boolean',
            'file_size' => 'integer',
            'duration' => 'float',
            'metadata' => 'array',
        ];
    }

    /**
     * Get the upload that this stem belongs to.
     */
    public function upload(): BelongsTo
    {
        return $this->belongsTo(Upload::class);
    }

    /**
     * Get the human-readable stem type name.
     */
    public function getStemTypeName(): string
    {
        return match ($this->stem_type) {
            'vocals' => 'Vocals',
            'drums' => 'Drums',
            'bass' => 'Bass',
            'guitar' => 'Guitar',
            'piano' => 'Piano',
            'other' => 'Other Instruments',
            default => ucfirst($this->stem_type)
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
     * Check if the stem file is stored locally.
     */
    public function isStoredLocally(): bool
    {
        return $this->storage_type === 'local';
    }

    /**
     * Check if the stem file is stored on R2.
     */
    public function isStoredOnR2(): bool
    {
        return $this->storage_type === 'r2';
    }
}
