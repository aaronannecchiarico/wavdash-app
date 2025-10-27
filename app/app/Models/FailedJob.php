<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class FailedJob extends Model
{
    /**
     * The table associated with the model.
     */
    protected $table = 'failed_jobs';

    /**
     * The primary key for the model.
     */
    protected $primaryKey = 'id';

    /**
     * Indicates if the model should be timestamped.
     */
    public $timestamps = false;

    /**
     * The attributes that should be cast.
     */
    protected $casts = [
        'failed_at' => 'datetime',
        'payload' => 'array',
    ];

    /**
     * The attributes that aren't mass assignable.
     */
    protected $guarded = ['id'];

    /**
     * Get the job class name from the payload.
     */
    public function getJobClassAttribute(): ?string
    {
        if (is_array($this->payload) && isset($this->payload['displayName'])) {
            return $this->payload['displayName'];
        }

        if (is_array($this->payload) && isset($this->payload['job'])) {
            $job = unserialize($this->payload['job']);

            return get_class($job);
        }

        return null;
    }

    /**
     * Get a short exception message.
     */
    public function getShortExceptionAttribute(): string
    {
        if (! $this->exception) {
            return 'No exception message';
        }

        $lines = explode("\n", $this->exception);

        return $lines[0] ?? 'Unknown exception';
    }
}
