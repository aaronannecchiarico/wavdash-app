<?php

namespace App\Services;

use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class AudioProcessingService
{
    /**
     * Client-side processing is always used.
     */
    public function shouldUseClientSideProcessing(): bool
    {
        // Always use client-side processing
        return true;
    }

    /**
     * Log performance metrics for audio processing.
     *
     * @param  array<string, mixed>  $metrics
     */
    public function logPerformanceMetrics(array $metrics): void
    {
        $user = Auth::user();
        $baseData = [
            'user_id' => $user?->id,
            'timestamp' => now()->toISOString(),
        ];

        Log::info('Audio processing performance metrics', array_merge($baseData, $metrics));
    }

    /**
     * Log processing error.
     * No fallback - client-side processing is required.
     */
    public function logProcessingError(string $error, string $processingType): bool
    {
        $user = Auth::user();

        Log::error('Audio processing error', [
            'user_id' => $user?->id,
            'processing_type' => $processingType,
            'error' => $error,
            'timestamp' => now()->toISOString(),
        ]);

        return false;
    }

    /**
     * Log processing success with metrics.
     * Always log success and performance metrics.
     *
     * @param  array<string, mixed>  $data
     */
    public function logProcessingSuccess(array $data): void
    {
        $user = Auth::user();

        $logData = array_merge([
            'user_id' => $user?->id,
            'timestamp' => now()->toISOString(),
            'phase' => 4,
        ], $data);

        Log::info('Audio processing success', $logData);

        $this->logPerformanceMetrics($data);
    }

    /**
     * Get processing configuration for the frontend.
     * Simplified config - always client-side processing.
     *
     * @return array{client_side_processing_enabled: bool, should_use_client_processing: bool, monitor_performance: bool}
     */
    public function getFrontendConfig(): array
    {
        return [
            'client_side_processing_enabled' => true,
            'should_use_client_processing' => true,
            'monitor_performance' => true,
        ];
    }
}
