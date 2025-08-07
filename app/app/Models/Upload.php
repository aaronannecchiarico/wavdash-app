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
}
