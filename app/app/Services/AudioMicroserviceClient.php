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
     */
    public function extractFeatures(string $storagePath, array $options = []): array
    {
        $response = Http::timeout(30)->asJson()->post("{$this->baseUrl}/storage/extract-features", [
            'storage_path' => $storagePath,
            'extract_detailed' => $options['detailed'] ?? false,
            'callback_url' => $options['callback_url'] ?? null,
            'metadata' => $options['metadata'] ?? []
        ]);
        
        if ($response->failed()) {
            throw new \Exception("Microservice error: " . $response->body());
        }
        
        return $response->json();
    }
    
    /**
     * Separate stems from an audio file using the new storage-based API.
     */
    public function separateStems(string $storagePath, array $options = []): array
    {
        $response = Http::timeout(30)->asJson()->post("{$this->baseUrl}/storage/separate-stems", [
            'storage_path' => $storagePath,
            'model_name' => $options['model'] ?? 'htdemucs',
            'callback_url' => $options['callback_url'] ?? null,
            'metadata' => $options['metadata'] ?? []
        ]);
        
        if ($response->failed()) {
            throw new \Exception("Microservice error: " . $response->body());
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
            throw new \Exception("Failed to get task summary: " . $response->body());
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
            throw new \Exception("Failed to get task status: " . $response->body());
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
            throw new \Exception("Storage status check failed: " . $response->body());
        }
        
        return $response->json();
    }
    
    /**
     * Check if the analysis service is available.
     */
    public function isServiceAvailable(): bool
    {
        try {
            $response = Http::timeout(5)->get($this->baseUrl . '/health');
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
        $response = Http::timeout(10)->get("{$this->baseUrl}/storage/file-info/" . urlencode($storagePath));
        
        if ($response->failed()) {
            throw new \Exception("Failed to get file info: " . $response->body());
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
            'max_keys' => $maxKeys
        ]);
        
        if ($response->failed()) {
            throw new \Exception("Failed to list files: " . $response->body());
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
            throw new \Exception("Failed to delete task: " . $response->body());
        }
        
        return $response->json();
    }
}