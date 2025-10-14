<?php

namespace App\Filament\Pages;

use App\Filament\Widgets\UploadsChart;
use App\Filament\Widgets\UserActivityOverview;
use App\Models\Upload;
use App\Models\User;
use BackedEnum;
use Filament\Infolists\Components\RepeatableEntry;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Concerns\InteractsWithInfolists;
use Filament\Infolists\Contracts\HasInfolists;
use Filament\Pages\Page;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Filament\Support\Enums\FontWeight;
use Illuminate\Support\Facades\DB;
use UnitEnum;

class AnalyticsDashboard extends Page implements HasInfolists
{
    use InteractsWithInfolists;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-chart-bar';

    protected string $view = 'filament.pages.analytics-dashboard';

    protected static ?string $navigationLabel = 'Analytics';

    protected static ?string $title = 'Analytics Dashboard';

    protected static string|UnitEnum|null $navigationGroup = 'System';

    protected static ?int $navigationSort = 2;

    /**
     * @return array<string, mixed>
     */
    protected function getHeaderWidgets(): array
    {
        return [
            UserActivityOverview::class,
        ];
    }

    /**
     * @return array<string, mixed>
     */
    protected function getFooterWidgets(): array
    {
        return [
            UploadsChart::class,
        ];
    }

    /**
     * @return array<string, mixed>
     */
    protected function getViewData(): array
    {
        return [
            'uploadTrends' => $this->getUploadTrends(),
            'userGrowth' => $this->getUserGrowth(),
            'topUsers' => $this->getTopUsers(),
            'genreStats' => $this->getGenreStats(),
        ];
    }

    /**
     * @return array<string, mixed>
     */
    private function getUploadTrends(): array
    {
        // Get uploads for the last 12 months
        $trends = Upload::query()
            ->select(DB::raw($this->getDateFormatSql('created_at', 'month')), DB::raw('count(*) as count'))
            ->where('created_at', '>=', now()->subYear())
            ->groupBy('month')
            ->orderBy('month')
            ->get()
            ->keyBy('month');

        $labels = [];
        $data = [];

        for ($i = 11; $i >= 0; $i--) {
            $month = now()->subMonths($i)->format('Y-m');
            $monthLabel = now()->subMonths($i)->format('M Y');
            $labels[] = $monthLabel;
            $data[] = $trends->get($month)->count ?? 0;
        }

        return compact('labels', 'data');
    }

    /**
     * @return array<string, mixed>
     */
    private function getUserGrowth(): array
    {
        // Get user registrations for the last 12 months
        $growth = User::query()
            ->select(DB::raw($this->getDateFormatSql('created_at', 'month')), DB::raw('count(*) as count'))
            ->where('created_at', '>=', now()->subYear())
            ->groupBy('month')
            ->orderBy('month')
            ->get()
            ->keyBy('month');

        $labels = [];
        $data = [];
        $cumulative = 0;

        for ($i = 11; $i >= 0; $i--) {
            $month = now()->subMonths($i)->format('Y-m');
            $monthLabel = now()->subMonths($i)->format('M Y');
            $labels[] = $monthLabel;
            $monthlyGrowth = $growth->get($month)->count ?? 0;
            $cumulative += $monthlyGrowth;
            $data[] = $cumulative;
        }

        return compact('labels', 'data');
    }

    /**
     * @return array<string, mixed>
     */
    public function getTopUsers(): array
    {
        return User::withCount('uploads')
            ->orderBy('uploads_count', 'desc')
            ->limit(10)
            ->get()
            ->map(function ($user) {
                return [
                    'name' => $user->name,
                    'email' => $user->email,
                    'uploads_count' => $user->uploads_count,
                ];
            })
            ->toArray();
    }

    public function topContributorsInfolist(Schema $schema): Schema
    {
        $topUsers = collect($this->getTopUsers());

        return $schema
            ->state(['top_users' => $topUsers])
            ->components([
                Section::make('Top Contributors')
                    ->description('Most active users in the platform')
                    ->icon('heroicon-o-users')
                    ->schema([
                        RepeatableEntry::make('top_users')
                            ->label('')
                            ->schema([
                                TextEntry::make('name')
                                    ->label('Name')
                                    ->icon('heroicon-m-user')
                                    ->weight(FontWeight::SemiBold)
                                    ->color('primary'),

                                TextEntry::make('email')
                                    ->label('Email')
                                    ->icon('heroicon-m-envelope')
                                    ->color('gray'),

                                TextEntry::make('uploads_count')
                                    ->label('Uploads')
                                    ->badge()
                                    ->color('success')
                                    ->icon('heroicon-m-musical-note'),
                            ])
                            ->columns(3)
                            ->contained(false)
                            ->extraAttributes(['class' => 'gap-4']),
                    ]),
            ]);
    }

    public function uploadTrendsInfolist(Schema $schema): Schema
    {
        $uploadTrends = $this->getUploadTrends();

        return $schema
            ->state(['uploadTrends' => $uploadTrends])
            ->components([
                Section::make('Monthly Upload Trends')
                    ->description('Upload activity over the last 12 months')
                    ->icon('heroicon-o-chart-bar')
                    ->schema([
                        TextEntry::make('debug')
                            ->label('Debug Info')
                            ->formatStateUsing(function () use ($uploadTrends) {
                                return 'Upload trends data: '.count($uploadTrends['labels']).' months, '.array_sum($uploadTrends['data']).' total uploads';
                            }),
                        TextEntry::make('uploadTrends.chart')
                            ->label('Chart')
                            ->formatStateUsing(function () use ($uploadTrends) {
                                return view('filament.infolists.components.upload-trends-chart', [
                                    'uploadTrends' => $uploadTrends,
                                ]);
                            }),
                    ]),
            ]);
    }

    public function userGrowthInfolist(Schema $schema): Schema
    {
        $userGrowth = $this->getUserGrowth();

        return $schema
            ->state(['userGrowth' => $userGrowth])
            ->components([
                Section::make('User Growth')
                    ->description('Cumulative user registrations over time')
                    ->icon('heroicon-o-users')
                    ->schema([
                        TextEntry::make('userGrowth.chart')
                            ->label('')
                            ->formatStateUsing(function () use ($userGrowth) {
                                return view('filament.infolists.components.user-growth-chart', [
                                    'userGrowth' => $userGrowth,
                                ]);
                            }),
                    ]),
            ]);
    }

    public function genreStatsInfolist(Schema $schema): Schema
    {
        $genreStats = $this->getGenreStats();

        // Only show if there's data
        if (empty($genreStats['labels'])) {
            return $schema->components([]);
        }

        return $schema
            ->state(['genreStats' => $genreStats])
            ->components([
                Section::make('Genre Distribution')
                    ->description('Popular music genres on the platform')
                    ->icon('heroicon-o-musical-note')
                    ->schema([
                        TextEntry::make('genreStats.chart')
                            ->label('')
                            ->formatStateUsing(function () use ($genreStats) {
                                return view('filament.infolists.components.genre-stats-chart', [
                                    'genreStats' => $genreStats,
                                ]);
                            }),
                    ]),
            ]);
    }

    /**
     * @return array<string, mixed>
     */
    private function getGenreStats(): array
    {
        $stats = Upload::query()
            ->select('genre', DB::raw('count(*) as count'))
            ->whereNotNull('genre')
            ->where('genre', '!=', '')
            ->groupBy('genre')
            ->orderBy('count', 'desc')
            ->limit(10)
            ->get();

        return [
            'labels' => $stats->pluck('genre')->toArray(),
            'data' => $stats->pluck('count')->toArray(),
        ];
    }

    /**
     * Get database-specific date formatting SQL for grouping by month
     */
    private function getDateFormatSql(string $column, string $alias): string
    {
        $driver = config('database.connections.'.config('database.default').'.driver');

        return match ($driver) {
            'sqlite' => "strftime('%Y-%m', {$column}) as {$alias}",
            'pgsql' => "to_char({$column}, 'YYYY-MM') as {$alias}",
            'mysql', 'mariadb' => "DATE_FORMAT({$column}, '%Y-%m') as {$alias}",
            default => "DATE_FORMAT({$column}, '%Y-%m') as {$alias}", // Default to MySQL
        };
    }
}
