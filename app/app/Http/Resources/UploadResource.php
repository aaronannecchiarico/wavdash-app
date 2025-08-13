<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;
use Illuminate\Support\Facades\Storage;

class UploadResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'description' => $this->description,
            'filename' => $this->filename,
            'mime_type' => $this->mime_type,
            'size' => $this->size,
            'status' => $this->status,
            'duration' => $this->duration_seconds,
            'stream_url' => $this->when($this->stream_path && $this->status === 'ready',
                function() {
                    // For R2 storage, getStreamPath returns the full URL
                    if ($this->usesR2Storage()) {
                        return $this->getStreamPath();
                    }
                    // For local storage, use Storage::url() to get proper public URL
                    return Storage::url($this->stream_path);
                }),
            'created_at' => $this->created_at,
            'updated_at' => $this->updated_at,
            'user' => [
                'id' => $this->user->id,
                'name' => $this->user->name,
            ],
            'analysis_task' => $this->when($this->relationLoaded('analysisTask') && $this->analysisTask, [
                'id' => $this->analysisTask?->id,
                'task_id' => $this->analysisTask?->task_id,
                'status' => $this->analysisTask?->status,
                'progress' => $this->analysisTask?->progress,
                'submitted_at' => $this->analysisTask?->submitted_at,
                'completed_at' => $this->analysisTask?->completed_at,
                'error_message' => $this->analysisTask?->error_message,
            ]),
            'analysis' => $this->when($this->relationLoaded('analysis') && $this->analysis, [
                'id' => $this->analysis?->id,
                'musical_key' => $this->analysis?->musical_key,
                'key_confidence' => $this->analysis?->key_confidence,
                'bpm' => $this->analysis?->bpm,
                'beat_regularity' => $this->analysis?->beat_regularity,
                'loudness_db' => $this->analysis?->loudness_db,
                'dynamic_range_db' => $this->analysis?->dynamic_range_db,
                'brightness' => $this->analysis?->brightness,
                'timbral_complexity' => $this->analysis?->timbral_complexity,
                'analysis_duration' => $this->analysis?->analysis_duration,
                'chunk_count' => $this->analysis?->chunk_count,
                'key_changes' => $this->analysis?->key_changes,
                'created_at' => $this->analysis?->created_at,
                'categories' => $this->when($this->analysis, [
                    'bpm' => $this->analysis?->getBpmCategory(),
                    'loudness' => $this->analysis?->getLoudnessCategory(),
                    'dynamic_range' => $this->analysis?->getDynamicRangeCategory(),
                    'brightness' => $this->analysis?->getBrightnessCategory(),
                ]),
                'reliability' => $this->when($this->analysis, [
                    'has_reliable_key' => $this->analysis?->hasReliableKey(),
                    'is_atonal_complex' => $this->analysis?->isAtonalComplex(),
                ]),
            ]),
            'has_analysis' => $this->relationLoaded('analysis') && $this->analysis !== null,
            'is_analysis_in_progress' => $this->when(
                $this->relationLoaded('analysisTask'),
                $this->analysisTask?->isProcessing() ?? false
            ),
        ];
    }
}
