<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Upload extends Model
{
    use HasFactory;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<string, mixed>
     */
    protected $fillable = [
        'user_id',
        'title',
        'description',
        'genre',
        'filename',
        'path',
        'stream_path',
        'mime_type',
        'size',
        'status',
        'duration_seconds',
        'r2_upload_path',
        'r2_stems_paths',
        'r2_analysis_path',
        'r2_uploaded_at',
        'uses_r2_storage',
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
            'user_id' => 'integer',
            'duration_seconds' => 'integer',
            'r2_stems_paths' => 'array',
            'r2_uploaded_at' => 'datetime',
            'uses_r2_storage' => 'boolean',
        ];
    }

    /**
     * Get the user that owns the upload.
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get the contest entries using this upload.
     */
    public function contestEntries(): HasMany
    {
        return $this->hasMany(ContestUser::class);
    }

    /**
     * Get the analysis task for this upload.
     */
    public function analysisTask(): HasOne
    {
        return $this->hasOne(UploadAnalysisTask::class);
    }

    /**
     * Get the analysis results for this upload.
     */
    public function analysis(): HasOne
    {
        return $this->hasOne(UploadAnalysis::class);
    }

    /**
     * Get the stem task for this upload.
     */
    public function stemTask(): HasOne
    {
        return $this->hasOne(UploadStemTask::class);
    }

    /**
     * Get the stems for this upload.
     */
    public function stems(): HasMany
    {
        return $this->hasMany(UploadStem::class);
    }

    /**
     * Get the tempo task for this upload.
     */
    public function tempoTask(): HasOne
    {
        return $this->hasOne(UploadTempoTask::class);
    }

    /**
     * Get the tempo variations for this upload.
     */
    public function tempos(): HasMany
    {
        return $this->hasMany(UploadTempo::class);
    }

    /**
     * Check if this upload has analysis results.
     */
    public function hasAnalysis(): bool
    {
        return $this->analysis !== null;
    }

    /**
     * Check if analysis is in progress.
     */
    public function isAnalysisInProgress(): bool
    {
        return $this->analysisTask && $this->analysisTask->isProcessing();
    }

    /**
     * Check if this upload has stems.
     */
    public function hasStems(): bool
    {
        return $this->stems()->exists();
    }

    /**
     * Check if stem separation is in progress.
     */
    public function isStemSeparationInProgress(): bool
    {
        return $this->stemTask && $this->stemTask->isProcessing();
    }

    /**
     * Check if this upload has tempo variations.
     */
    public function hasTempos(): bool
    {
        return $this->tempos()->exists();
    }

    /**
     * Check if tempo processing is in progress.
     */
    public function isTempoProcessingInProgress(): bool
    {
        return $this->tempoTask && $this->tempoTask->isProcessing();
    }

    /**
     * Check if this upload uses R2 storage.
     */
    public function usesR2Storage(): bool
    {
        return $this->uses_r2_storage && ! empty($this->r2_upload_path);
    }

    /**
     * Get the appropriate file path based on storage type.
     */
    public function getFilePath(): string
    {
        return $this->usesR2Storage() ? $this->r2_upload_path : $this->path;
    }

    /**
     * Get the appropriate stream path based on storage type.
     */
    public function getStreamPath(): ?string
    {
        if ($this->usesR2Storage() && config('filesystems.disks.r2.url')) {
            return config('filesystems.disks.r2.url').'/'.$this->r2_upload_path;
        }

        return $this->stream_path;
    }

    /**
     * Check if this upload has R2 stems.
     */
    public function hasR2Stems(): bool
    {
        return $this->usesR2Storage() && ! empty($this->r2_stems_paths);
    }
}
