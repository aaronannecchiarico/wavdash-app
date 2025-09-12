<?php

namespace App\Services;

use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class AudioProcessingService
{
    /**
     * Determine if a user should get client-side audio processing based on A/B testing rules.
     */
    public function shouldUseClientSideProcessing(): bool
    {
        // If client-side processing is globally enabled, use it
        if (config('app.client_side_audio_processing')) {
            return true;
        }

        // If A/B testing is not enabled, use server-side processing
        if (!config('app.audio_processing_ab_test.enabled')) {
            return false;
        }

        $user = Auth::user();
        if (!$user) {
            return false;
        }

        // Use user ID to consistently assign them to the same group
        $userHash = crc32($user->id);
        $userPercentile = abs($userHash) % 100;
        $clientPercentage = config('app.audio_processing_ab_test.client_percentage', 50);

        $shouldUseClient = $userPercentile < $clientPercentage;

        // Log A/B test assignment if monitoring is enabled
        if (config('app.audio_processing_ab_test.monitor_performance')) {
            Log::info('Audio processing A/B test assignment', [
                'user_id' => $user->id,
                'assigned_to_client' => $shouldUseClient,
                'user_percentile' => $userPercentile,
                'client_percentage_threshold' => $clientPercentage,
            ]);
        }

        return $shouldUseClient;
    }

    /**
     * Log performance metrics for audio processing.
     */
    public function logPerformanceMetrics(array $metrics): void
    {
        if (!config('app.audio_processing_ab_test.monitor_performance')) {
            return;
        }

        $user = Auth::user();
        $baseData = [
            'user_id' => $user?->id,
            'timestamp' => now()->toISOString(),
        ];

        Log::info('Audio processing performance metrics', array_merge($baseData, $metrics));
    }

    /**
     * Log processing error and determine if fallback should be used.
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

        // Return whether fallback should be used for client-side errors
        return $processingType === 'client' && config('app.audio_processing_ab_test.fallback_on_error', true);
    }

    /**
     * Log processing success with metrics.
     */
    public function logProcessingSuccess(array $data): void
    {
        $user = Auth::user();
        
        $logData = array_merge([
            'user_id' => $user?->id,
            'timestamp' => now()->toISOString(),
        ], $data);

        Log::info('Audio processing success', $logData);

        // Also log as performance metrics if monitoring is enabled
        if (config('app.audio_processing_ab_test.monitor_performance')) {
            $this->logPerformanceMetrics($data);
        }
    }

    /**
     * Get processing configuration for the frontend.
     */
    public function getFrontendConfig(): array
    {
        return [
            'client_side_processing_enabled' => config('app.client_side_audio_processing'),
            'ab_test_enabled' => config('app.audio_processing_ab_test.enabled'),
            'should_use_client_processing' => $this->shouldUseClientSideProcessing(),
            'fallback_on_error' => config('app.audio_processing_ab_test.fallback_on_error'),
            'monitor_performance' => config('app.audio_processing_ab_test.monitor_performance'),
        ];
    }
}