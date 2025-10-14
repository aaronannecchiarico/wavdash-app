<?php

namespace App\Filament\Widgets;

use App\Models\Upload;
use Filament\Widgets\ChartWidget;
use Illuminate\Support\Facades\DB;

class UploadsChart extends ChartWidget
{
    protected ?string $heading = 'Daily Uploads (Last 30 Days)';

    /**
     * @return array<string, mixed>
     */
    protected function getData(): array
    {
        // Get the last 30 days of data
        $data = Upload::query()
            ->select(DB::raw('DATE(created_at) as date'), DB::raw('count(*) as count'))
            ->where('created_at', '>=', now()->subDays(30))
            ->groupBy('date')
            ->orderBy('date')
            ->get();

        // Create an array for all 30 days
        $labels = [];
        $uploadCounts = [];

        for ($i = 29; $i >= 0; $i--) {
            $date = now()->subDays($i)->format('Y-m-d');
            $labels[] = now()->subDays($i)->format('M j');

            // Find the count for this date
            $dayData = $data->firstWhere('date', $date);
            $uploadCounts[] = $dayData ? $dayData->count : 0;
        }

        return [
            'datasets' => [
                [
                    'label' => 'Uploads',
                    'data' => $uploadCounts,
                    'borderColor' => '#f59e0b',
                    'backgroundColor' => 'rgba(245, 158, 11, 0.1)',
                    'fill' => true,
                    'tension' => 0.3,
                ],
            ],
            'labels' => $labels,
        ];
    }

    protected function getType(): string
    {
        return 'line';
    }

    /**
     * @return array<string, mixed>
     */
    protected function getOptions(): array
    {
        return [
            'plugins' => [
                'legend' => [
                    'display' => false,
                ],
            ],
            'scales' => [
                'y' => [
                    'beginAtZero' => true,
                    'ticks' => [
                        'precision' => 0,
                    ],
                ],
            ],
        ];
    }
}
