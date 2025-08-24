<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;
use Illuminate\Support\Facades\Storage;

class UploadResource extends JsonResource
{
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
                function () {
                    if ($this->usesR2Storage()) {
                        return $this->getStreamPath();
                    }

                    return Storage::disk('public')->url($this->stream_path);
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
            'stem_task' => $this->when($this->relationLoaded('stemTask') && $this->stemTask, [
                'id' => $this->stemTask?->id,
                'task_id' => $this->stemTask?->task_id,
                'status' => $this->stemTask?->status,
                'progress' => $this->stemTask?->progress,
                'submitted_at' => $this->stemTask?->submitted_at,
                'completed_at' => $this->stemTask?->completed_at,
                'error_message' => $this->stemTask?->error_message,
            ]),
            'tempo_task' => $this->when($this->relationLoaded('tempoTask') && $this->tempoTask, [
                'id' => $this->tempoTask?->id,
                'task_id' => $this->tempoTask?->task_id,
                'status' => $this->tempoTask?->status,
                'progress' => $this->tempoTask?->progress,
                'submitted_at' => $this->tempoTask?->submitted_at,
                'completed_at' => $this->tempoTask?->completed_at,
                'error_message' => $this->tempoTask?->error_message,
                'processing_options' => $this->tempoTask?->processing_options,
            ]),
            'stems' => $this->when($this->relationLoaded('stems'), function () {
                return $this->stems->map(function ($stem) {
                    return [
                        'id' => $stem->id,
                        'stem_type' => $stem->stem_type,
                        'stem_type_name' => $stem->getStemTypeName(),
                        'file_path' => $stem->file_path,
                        'public_path' => $stem->public_path,
                        'storage_type' => $stem->storage_type,
                        'file_size' => $stem->file_size,
                        'formatted_file_size' => $stem->getFormattedFileSize(),
                        'duration' => $stem->duration,
                        'formatted_duration' => $stem->getFormattedDuration(),
                        'metadata' => $stem->metadata,
                        'created_at' => $stem->created_at,
                    ];
                });
            }),
            'tempos' => $this->when($this->relationLoaded('tempos'), function () {
                return $this->tempos->map(function ($tempo) {
                    return [
                        'id' => $tempo->id,
                        'preset' => $tempo->preset,
                        'preset_name' => $tempo->getPresetName(),
                        'tempo_factor' => $tempo->tempo_factor,
                        'pitch_shift_semitones' => $tempo->pitch_shift_semitones,
                        'preserve_pitch' => $tempo->preserve_pitch,
                        'add_reverb' => $tempo->add_reverb,
                        'use_stems' => $tempo->use_stems,
                        'file_path' => $tempo->file_path,
                        'public_path' => $tempo->public_path,
                        'storage_type' => $tempo->storage_type,
                        'file_size' => $tempo->file_size,
                        'formatted_file_size' => $tempo->getFormattedFileSize(),
                        'duration' => $tempo->duration,
                        'formatted_duration' => $tempo->getFormattedDuration(),
                        'final_bpm' => $tempo->final_bpm,
                        'tempo_description' => $tempo->getTempoDescription(),
                        'pitch_description' => $tempo->getPitchDescription(),
                        'processing_metadata' => $tempo->processing_metadata,
                        'created_at' => $tempo->created_at,
                    ];
                });
            }),
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
            'has_stems' => $this->relationLoaded('stems') && $this->stems->count() > 0,
            'is_stem_separation_in_progress' => $this->when(
                $this->relationLoaded('stemTask'),
                $this->stemTask?->isProcessing() ?? false
            ),
            'has_tempos' => $this->relationLoaded('tempos') && $this->tempos->count() > 0,
            'is_tempo_processing_in_progress' => $this->when(
                $this->relationLoaded('tempoTask'),
                $this->tempoTask?->isProcessing() ?? false
            ),
        ];
    }
}
