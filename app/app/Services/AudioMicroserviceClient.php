<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AudioMicroserviceClient
{
    protected string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('services.audio_analysis.base_url', 'http://localhost:8001'), '/');
    }

    /**
     * Extract features from an audio file using the new storage-based API.
     *
     * @param  array<string, mixed>  $options
     */
    public function extractFeatures(string $storagePath, array $options = []): array
    {
        $response = Http::timeout(30)->asJson()->post("{$this->baseUrl}/storage/extract-features", [
            'storage_path' => $storagePath,
            'extract_detailed' => $options['detailed'] ?? false,
            'callback_url' => $options['callback_url'] ?? null,
            'metadata' => $options['metadata'] ?? [],
        ]);

        if ($response->failed()) {
            throw new \Exception('Microservice error: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Separate stems from an audio file using the new storage-based API.
     *
     * @param  array<string, mixed>  $options
     */
    public function separateStems(string $storagePath, array $options = []): array
    {
        $response = Http::timeout(30)->asJson()->post("{$this->baseUrl}/storage/separate-stems", [
            'storage_path' => $storagePath,
            'model_name' => $options['model'] ?? 'htdemucs',
            'callback_url' => $options['callback_url'] ?? null,
            'metadata' => $options['metadata'] ?? [],
        ]);

        if ($response->failed()) {
            throw new \Exception('Microservice error: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Get task summary from the microservice.
     */
    public function getTaskSummary(string $taskId): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/task-summary/{$taskId}");

        if ($response->failed()) {
            throw new \Exception('Failed to get task summary: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Get task status from the microservice.
     */
    public function getTaskStatus(string $taskId): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/task-status/{$taskId}");

        if ($response->failed()) {
            throw new \Exception('Failed to get task status: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Get storage status from the microservice.
     */
    public function getStorageStatus(): array
    {
        $response = Http::timeout(5)->get("{$this->baseUrl}/storage/status");

        if ($response->failed()) {
            throw new \Exception('Storage status check failed: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Check if the analysis service is available.
     */
    public function isServiceAvailable(): bool
    {
        try {
            $response = Http::timeout(5)->get($this->baseUrl.'/health');

            return $response->successful() && $response->json('status') === 'healthy';
        } catch (\Exception $e) {
            Log::warning('Audio analysis service unavailable', ['error' => $e->getMessage()]);

            return false;
        }
    }

    /**
     * Get file information from storage.
     */
    public function getFileInfo(string $storagePath): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/storage/file-info/".urlencode($storagePath));

        if ($response->failed()) {
            throw new \Exception('Failed to get file info: '.$response->body());
        }

        return $response->json();
    }

    /**
     * List files in storage.
     */
    public function listFiles(string $prefix = '', int $maxKeys = 100): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/storage/list-files", [
            'prefix' => $prefix,
            'max_keys' => $maxKeys,
        ]);

        if ($response->failed()) {
            throw new \Exception('Failed to list files: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Delete a task from the microservice.
     */
    public function deleteTask(string $taskId): array
    {
        $response = Http::timeout(10)->delete("{$this->baseUrl}/task/{$taskId}");

        if ($response->failed()) {
            throw new \Exception('Failed to delete task: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Process tempo effects on an audio file using the storage-based API.
     *
     * @param  array<string, mixed>  $options
     */
    public function processTempo(string $storagePath, array $options = []): array
    {
        $payload = [
            'storage_path' => $storagePath,
            'callback_url' => $options['callback_url'] ?? null,
            'metadata' => $options['metadata'] ?? [],
        ];

        // Add tempo processing options if provided
        if (isset($options['preset'])) {
            $payload['preset_name'] = $options['preset'];
        }
        if (isset($options['tempo_factor'])) {
            $payload['tempo_factor'] = (float) $options['tempo_factor'];
        }
        if (isset($options['pitch_shift_semitones'])) {
            $payload['pitch_shift_semitones'] = (float) $options['pitch_shift_semitones'];
        }
        if (isset($options['preserve_pitch'])) {
            $payload['preserve_pitch'] = (bool) $options['preserve_pitch'];
        }
        if (isset($options['add_reverb'])) {
            $payload['add_reverb'] = (bool) $options['add_reverb'];
        }
        if (isset($options['use_stems'])) {
            $payload['use_stems'] = (bool) $options['use_stems'];
        }

        Log::info('Sending tempo processing request to microservice', [
            'url' => "{$this->baseUrl}/tempo/storage/process",
            'payload' => $payload,
        ]);

        $response = Http::timeout(30)->asJson()->post("{$this->baseUrl}/tempo/storage/process", $payload);

        if ($response->failed()) {
            Log::error('Tempo processing microservice request failed', [
                'url' => "{$this->baseUrl}/tempo/storage/process",
                'payload' => $payload,
                'status_code' => $response->status(),
                'response_body' => $response->body(),
            ]);
            throw new \Exception('Tempo processing microservice error: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Get available tempo processing presets.
     */
    public function getTempoPresets(): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/tempo/presets");

        if ($response->failed()) {
            throw new \Exception('Failed to get tempo presets: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Get smart tempo preset suggestions based on audio characteristics.
     *
     * @param  array<string, mixed>  $params
     */
    public function getTempoSuggestions(array $params = []): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/tempo/suggest-presets", $params);

        if ($response->failed()) {
            throw new \Exception('Failed to get tempo suggestions: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Check tempo processing system compatibility.
     */
    public function getTempoSystemCompatibility(): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/tempo/system/compatibility");

        if ($response->failed()) {
            throw new \Exception('Failed to get tempo system compatibility: '.$response->body());
        }

        return $response->json();
    }

    /**
     * Get tempo processing performance metrics.
     */
    public function getTempoPerformanceMetrics(): array
    {
        $response = Http::timeout(10)->get("{$this->baseUrl}/tempo/performance/metrics");

        if ($response->failed()) {
            throw new \Exception('Failed to get tempo performance metrics: '.$response->body());
        }

        return $response->json();
    }
}
