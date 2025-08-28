<?php

namespace App\Filament\Widgets;

use App\Models\Upload;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class UploadStatsOverview extends StatsOverviewWidget
{
    protected function getStats(): array
    {
        // Get upload statistics
        $totalUploads = Upload::count();
        $todayUploads = Upload::whereDate('created_at', today())->count();
        $weeklyUploads = Upload::whereBetween('created_at', [now()->subWeek(), now()])->count();
        $readyUploads = Upload::where('status', 'ready')->count();
        $processingUploads = Upload::where('status', 'processing')->count();
        $failedUploads = Upload::where('status', 'failed')->count();

        // Get total file size in a human readable format
        $totalSize = Upload::sum('size');
        $formattedSize = $this->formatBytes($totalSize);

        // Calculate average file size
        $avgSize = $totalUploads > 0 ? $totalSize / $totalUploads : 0;
        $formattedAvgSize = $this->formatBytes($avgSize);

        // Get percentage of successful uploads
        $successRate = $totalUploads > 0 ? round(($readyUploads / $totalUploads) * 100, 1) : 0;

        return [
            Stat::make('Total Uploads', number_format($totalUploads))
                ->description('All time uploads')
                ->descriptionIcon('heroicon-m-arrow-trending-up')
                ->color('primary'),

            Stat::make('Today\'s Uploads', number_format($todayUploads))
                ->description('Uploaded today')
                ->descriptionIcon('heroicon-m-calendar-days')
                ->color('info'),

            Stat::make('Weekly Uploads', number_format($weeklyUploads))
                ->description('Last 7 days')
                ->descriptionIcon('heroicon-m-chart-bar-square')
                ->color('success'),

            Stat::make('Total Storage', $formattedSize)
                ->description("Avg: {$formattedAvgSize} per file")
                ->descriptionIcon('heroicon-m-server')
                ->color('warning'),

            Stat::make('Success Rate', "{$successRate}%")
                ->description("{$readyUploads} ready, {$processingUploads} processing, {$failedUploads} failed")
                ->descriptionIcon('heroicon-m-check-circle')
                ->color($successRate >= 90 ? 'success' : ($successRate >= 70 ? 'warning' : 'danger')),
        ];
    }

    /**
     * Format bytes to human readable format
     */
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
