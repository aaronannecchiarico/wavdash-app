<?php

namespace App\Filament\Widgets;

use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;

class SystemHealthOverview extends StatsOverviewWidget
{
    protected function getStats(): array
    {
        // Queue statistics
        $pendingJobs = $this->getPendingJobsCount();
        $failedJobs = $this->getFailedJobsCount();

        // Storage statistics
        $storageUsage = $this->getStorageUsage();

        // Database connection test
        $dbStatus = $this->getDatabaseStatus();

        // Cache status
        $cacheStatus = $this->getCacheStatus();

        return [
            Stat::make('Queue Jobs', $pendingJobs)
                ->description($failedJobs > 0 ? "{$failedJobs} failed jobs" : 'All jobs healthy')
                ->descriptionIcon($failedJobs > 0 ? 'heroicon-m-exclamation-triangle' : 'heroicon-m-check-circle')
                ->color($failedJobs > 0 ? 'danger' : 'success'),

            Stat::make('Storage Usage', $storageUsage['formatted'])
                ->description("Free: {$storageUsage['free_formatted']}")
                ->descriptionIcon('heroicon-m-server-stack')
                ->color($storageUsage['usage_percent'] > 90 ? 'danger' : ($storageUsage['usage_percent'] > 75 ? 'warning' : 'success')),

            Stat::make('Database', $dbStatus['status'])
                ->description($dbStatus['description'])
                ->descriptionIcon($dbStatus['status'] === 'Connected' ? 'heroicon-m-check-circle' : 'heroicon-m-x-circle')
                ->color($dbStatus['status'] === 'Connected' ? 'success' : 'danger'),

            Stat::make('Cache', $cacheStatus['status'])
                ->description($cacheStatus['description'])
                ->descriptionIcon($cacheStatus['status'] === 'Working' ? 'heroicon-m-check-circle' : 'heroicon-m-x-circle')
                ->color($cacheStatus['status'] === 'Working' ? 'success' : 'danger'),
        ];
    }

    private function getPendingJobsCount(): int
    {
        try {
            return DB::table('jobs')->count();
        } catch (\Exception $e) {
            return 0;
        }
    }

    private function getFailedJobsCount(): int
    {
        try {
            return DB::table('failed_jobs')->count();
        } catch (\Exception $e) {
            return 0;
        }
    }

    private function getStorageUsage(): array
    {
        try {
            $disk = Storage::disk('local');
            $totalSpace = disk_total_space(storage_path());
            $freeSpace = disk_free_space(storage_path());
            $usedSpace = $totalSpace - $freeSpace;
            $usagePercent = $totalSpace > 0 ? round(($usedSpace / $totalSpace) * 100, 1) : 0;

            return [
                'used' => $usedSpace,
                'free' => $freeSpace,
                'total' => $totalSpace,
                'usage_percent' => $usagePercent,
                'formatted' => $this->formatBytes($usedSpace).' / '.$this->formatBytes($totalSpace),
                'free_formatted' => $this->formatBytes($freeSpace),
            ];
        } catch (\Exception $e) {
            return [
                'used' => 0,
                'free' => 0,
                'total' => 0,
                'usage_percent' => 0,
                'formatted' => 'Unknown',
                'free_formatted' => 'Unknown',
            ];
        }
    }

    private function getDatabaseStatus(): array
    {
        try {
            DB::connection()->getPdo();
            $tableCount = $this->getTableCount();

            return [
                'status' => 'Connected',
                'description' => "{$tableCount} tables",
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'Disconnected',
                'description' => 'Connection failed',
            ];
        }
    }

    private function getTableCount(): int
    {
        try {
            $driver = config('database.connections.'.config('database.default').'.driver');

            if ($driver === 'sqlite') {
                return collect(DB::select("SELECT name FROM sqlite_master WHERE type='table'"))->count();
            } elseif (in_array($driver, ['mysql', 'mariadb'])) {
                return collect(DB::select('SHOW TABLES'))->count();
            } elseif ($driver === 'pgsql') {
                return collect(DB::select("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))->count();
            }

            // Fallback: try to count from information_schema
            return collect(DB::select('SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()'))->count();
        } catch (\Exception $e) {
            // If all else fails, just return 0 - at least we know the connection works
            return 0;
        }
    }

    private function getCacheStatus(): array
    {
        try {
            $testKey = 'health_check_'.time();
            $testValue = 'working';

            Cache::put($testKey, $testValue, 60);
            $retrieved = Cache::get($testKey);
            Cache::forget($testKey);

            if ($retrieved === $testValue) {
                return [
                    'status' => 'Working',
                    'description' => 'Read/write successful',
                ];
            }

            return [
                'status' => 'Failed',
                'description' => 'Read/write failed',
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'Error',
                'description' => 'Cache unavailable',
            ];
        }
    }

    private function formatBytes(int $size, int $precision = 2): string
    {
        if ($size === 0) {
            return '0 B';
        }

        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        $base = log($size, 1024);
        $index = (int) floor($base);
        $value = round(pow(1024, $base - $index), $precision);

        return $value.' '.$units[$index];
    }
}
