<?php

namespace App\Filament\Widgets;

use App\Models\Upload;
use App\Models\User;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class UserActivityOverview extends StatsOverviewWidget
{
    protected function getStats(): array
    {
        // Total users
        $totalUsers = User::count();

        // Active users (users who uploaded in last 30 days)
        $activeUsers = User::whereHas('uploads', function ($query) {
            $query->where('created_at', '>=', now()->subDays(30));
        })->count();

        // New users today
        $newUsersToday = User::whereDate('created_at', today())->count();

        // Most active user
        $mostActiveUser = User::withCount(['uploads' => function ($query) {
            $query->where('created_at', '>=', now()->subDays(30));
        }])
            ->orderBy('uploads_count', 'desc')
            ->first();

        // Average uploads per user
        $avgUploadsPerUser = $totalUsers > 0 ? round(Upload::count() / $totalUsers, 1) : 0;

        return [
            Stat::make('Total Users', number_format($totalUsers))
                ->description("{$newUsersToday} joined today")
                ->descriptionIcon('heroicon-m-users')
                ->color('primary'),

            Stat::make('Active Users', number_format($activeUsers))
                ->description('Last 30 days ('.round($activeUsers / max($totalUsers, 1) * 100, 1).'%)')
                ->descriptionIcon('heroicon-m-user-group')
                ->color('success'),

            Stat::make('Avg. Uploads/User', $avgUploadsPerUser)
                ->description('All time average')
                ->descriptionIcon('heroicon-m-arrow-trending-up')
                ->color('info'),

            Stat::make('Most Active', $mostActiveUser ? $mostActiveUser->name : 'N/A')
                ->description($mostActiveUser ? "{$mostActiveUser->uploads_count} uploads (30d)" : 'No activity')
                ->descriptionIcon('heroicon-m-trophy')
                ->color('warning'),
        ];
    }
}
