<?php

namespace App\Filament\Pages;

use App\Filament\Widgets\SystemHealthOverview;
use BackedEnum;
use Filament\Infolists\Components\RepeatableEntry;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Concerns\InteractsWithInfolists;
use Filament\Infolists\Contracts\HasInfolists;
use Filament\Pages\Page;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Filament\Support\Enums\FontWeight;
use Filament\Support\Icons\Heroicon;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Storage;
use UnitEnum;

class SystemHealth extends Page implements HasInfolists
{
    use InteractsWithInfolists;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-heart';

    protected string $view = 'filament.pages.system-health';

    protected static ?string $navigationLabel = 'System Health';

    protected static ?string $title = 'System Health Monitor';

    protected static string|UnitEnum|null $navigationGroup = 'System';

    protected static ?int $navigationSort = 1;

    protected function getHeaderWidgets(): array
    {
        return [
            SystemHealthOverview::class,
        ];
    }

    public function servicesInfolist(Schema $schema): Schema
    {
        $services = collect($this->getServiceStatus())->values();

        return $schema
            ->state(['services' => $services])
            ->components([
                Section::make('Services Status')
                    ->description('Current status of all system services')
                    ->icon(Heroicon::Server)
                    ->schema([
                        RepeatableEntry::make('services')
                            ->label('')
                            ->schema([
                                TextEntry::make('name')
                                    ->label('Service')
                                    ->icon(Heroicon::Cog)
                                    ->weight(FontWeight::SemiBold)
                                    ->color('primary'),

                                TextEntry::make('description')
                                    ->label('Description')
                                    ->color('gray'),

                                TextEntry::make('status')
                                    ->label('Status')
                                    ->badge()
                                    ->color(fn (string $state): string => match ($state) {
                                        'healthy', 'running' => 'success',
                                        'warning' => 'warning',
                                        default => 'danger',
                                    })
                                    ->icon(fn (string $state): string|Heroicon => match ($state) {
                                        'healthy', 'running' => Heroicon::CheckBadge,
                                        'warning' => Heroicon::ExclamationTriangle,
                                        default => Heroicon::XCircle,
                                    }),
                            ])
                            ->columns(3)
                            ->contained(false)
                            ->extraAttributes(['class' => 'gap-4']),
                    ]),
            ]);
    }

    public function queueInfolist(Schema $schema): Schema
    {
        $queueData = $this->getQueueStatus();
        $queueItems = [
            [
                'name' => 'Pending Jobs',
                'value' => number_format($queueData['pending_jobs']),
                'description' => 'Jobs waiting in queue',
                'status' => $queueData['pending_jobs'] > 0 ? 'warning' : 'success',
                'icon' => Heroicon::Clock,
            ],
            [
                'name' => 'Failed Jobs',
                'value' => number_format($queueData['failed_jobs']),
                'description' => 'Jobs that have failed',
                'status' => $queueData['failed_jobs'] > 0 ? 'danger' : 'success',
                'icon' => Heroicon::XCircle,
            ],
            [
                'name' => 'Processed Jobs',
                'value' => number_format($queueData['processed_jobs']),
                'description' => 'Jobs ready to process',
                'status' => 'info',
                'icon' => Heroicon::CheckCircle,
            ],
        ];

        return $schema
            ->state(['queue_items' => $queueItems])
            ->components([
                Section::make('Queue Status')
                    ->description('Current queue processing status')
                    ->icon('heroicon-o-queue-list')
                    ->schema([
                        RepeatableEntry::make('queue_items')
                            ->label('')
                            ->schema([
                                TextEntry::make('name')
                                    ->label('Metric')
                                    ->icon(Heroicon::InformationCircle)
                                    ->weight(FontWeight::SemiBold)
                                    ->color('primary'),

                                TextEntry::make('value')
                                    ->label('Value')
                                    ->badge()
                                    ->color(function ($record) {
                                        if (is_null($record) || ! isset($record['status'])) {
                                            return 'info';
                                        }

                                        return match ($record['status']) {
                                            'success' => 'success',
                                            'warning' => 'warning',
                                            'danger' => 'danger',
                                            default => 'info',
                                        };
                                    }),

                                TextEntry::make('description')
                                    ->label('Description')
                                    ->color('gray'),
                            ])
                            ->columns(3)
                            ->contained(false)
                            ->extraAttributes(['class' => 'gap-4']),
                    ]),
            ]);
    }

    public function storageInfolist(Schema $schema): Schema
    {
        $storageData = $this->getStorageStatus();
        $storageItems = [
            [
                'name' => 'Used Space',
                'value' => number_format($storageData['used'] / 1024 / 1024 / 1024, 2).' GB',
                'description' => 'Currently used storage space',
                'status' => $storageData['usage_percent'] > 90 ? 'danger' : ($storageData['usage_percent'] > 75 ? 'warning' : 'success'),
                'icon' => Heroicon::ServerStack,
            ],
            [
                'name' => 'Free Space',
                'value' => number_format($storageData['free'] / 1024 / 1024 / 1024, 2).' GB',
                'description' => 'Available storage space',
                'status' => 'info',
                'icon' => Heroicon::Folder,
            ],
            [
                'name' => 'Usage Percentage',
                'value' => $storageData['usage_percent'].'%',
                'description' => 'Storage utilization ratio',
                'status' => $storageData['usage_percent'] > 90 ? 'danger' : ($storageData['usage_percent'] > 75 ? 'warning' : 'success'),
                'icon' => Heroicon::ChartPie,
            ],
            [
                'name' => 'Total Capacity',
                'value' => number_format($storageData['total'] / 1024 / 1024 / 1024, 2).' GB',
                'description' => 'Total storage capacity',
                'status' => 'info',
                'icon' => Heroicon::CpuChip,
            ],
        ];

        return $schema
            ->state(['storage_items' => $storageItems])
            ->components([
                Section::make('Storage Status')
                    ->description('Current storage usage and capacity')
                    ->icon(Heroicon::ServerStack)
                    ->schema([
                        RepeatableEntry::make('storage_items')
                            ->label('')
                            ->schema([
                                TextEntry::make('name')
                                    ->label('Metric')
                                    ->icon(fn ($record): string|Heroicon => $record['icon'] ?? Heroicon::InformationCircle)
                                    ->weight(FontWeight::SemiBold)
                                    ->color('primary'),

                                TextEntry::make('value')
                                    ->label('Value')
                                    ->badge()
                                    ->color(function ($record) {
                                        if (is_null($record) || ! isset($record['status'])) {
                                            return 'info';
                                        }

                                        return match ($record['status']) {
                                            'success' => 'success',
                                            'warning' => 'warning',
                                            'danger' => 'danger',
                                            default => 'info',
                                        };
                                    }),

                                TextEntry::make('description')
                                    ->label('Description')
                                    ->color('gray'),
                            ])
                            ->columns(3)
                            ->contained(false)
                            ->extraAttributes(['class' => 'gap-4']),
                    ]),
            ]);
    }

    public function databaseInfolist(Schema $schema): Schema
    {
        $databaseData = $this->getDatabaseStatus();
        $databaseItems = [];

        if ($databaseData['status'] === 'connected') {
            $databaseItems = [
                [
                    'name' => 'Connection Status',
                    'value' => 'Connected',
                    'description' => 'Database connection is healthy and operational',
                    'status' => 'success',
                    'icon' => Heroicon::CheckBadge,
                ],
                [
                    'name' => 'Connection Name',
                    'value' => $databaseData['connection_name'],
                    'description' => 'Current database connection configuration',
                    'status' => 'info',
                    'icon' => Heroicon::CircleStack,
                ],
                [
                    'name' => 'Table Count',
                    'value' => number_format($databaseData['tables_count']).' tables',
                    'description' => 'Total number of database tables',
                    'status' => 'info',
                    'icon' => Heroicon::TableCells,
                ],
            ];
        } else {
            $databaseItems = [
                [
                    'name' => 'Connection Status',
                    'value' => 'Disconnected',
                    'description' => $databaseData['error'] ?? 'Unable to establish database connection',
                    'status' => 'danger',
                    'icon' => Heroicon::XCircle,
                ],
            ];
        }

        return $schema
            ->state(['database_items' => $databaseItems])
            ->components([
                Section::make('Database Status')
                    ->description('Current database connection and information')
                    ->icon(Heroicon::CircleStack)
                    ->schema([
                        RepeatableEntry::make('database_items')
                            ->label('')
                            ->schema([
                                TextEntry::make('name')
                                    ->label('Metric')
                                    ->icon(fn ($record): string|Heroicon => $record['icon'] ?? Heroicon::InformationCircle)
                                    ->weight(FontWeight::SemiBold)
                                    ->color('primary'),

                                TextEntry::make('value')
                                    ->label('Value')
                                    ->badge()
                                    ->color(function ($record) {
                                        if (is_null($record) || ! isset($record['status'])) {
                                            return 'info';
                                        }

                                        return match ($record['status']) {
                                            'success' => 'success',
                                            'warning' => 'warning',
                                            'danger' => 'danger',
                                            default => 'info',
                                        };
                                    }),

                                TextEntry::make('description')
                                    ->label('Description')
                                    ->color('gray'),
                            ])
                            ->columns(3)
                            ->contained(false)
                            ->extraAttributes(['class' => 'gap-4']),
                    ]),
            ]);
    }

    protected function getViewData(): array
    {
        return [
            'services' => $this->getServiceStatus(),
            'queues' => $this->getQueueStatus(),
            'storage' => $this->getStorageStatus(),
            'database' => $this->getDatabaseStatus(),
        ];
    }

    private function getServiceStatus(): array
    {
        return [
            'web' => [
                'name' => 'Web Server',
                'status' => 'running',
                'description' => 'Laravel application is responding',
                'icon' => Heroicon::Server,
                'color' => 'success',
            ],
            'cache' => $this->checkCacheService(),
            'database' => $this->checkDatabaseService(),
            'storage' => $this->checkStorageService(),
        ];
    }

    private function checkCacheService(): array
    {
        try {
            $testKey = 'health_check_'.time();
            Cache::put($testKey, 'test', 60);
            $result = Cache::get($testKey);
            Cache::forget($testKey);

            return [
                'name' => 'Cache',
                'status' => $result === 'test' ? 'healthy' : 'warning',
                'description' => $result === 'test' ? 'Cache read/write working' : 'Cache issues detected',
                'icon' => Heroicon::CpuChip,
                'color' => $result === 'test' ? 'success' : 'warning',
            ];
        } catch (\Exception $e) {
            return [
                'name' => 'Cache',
                'status' => 'error',
                'description' => 'Cache service unavailable',
                'icon' => 'heroicon-o-cpu-chip',
                'color' => 'danger',
            ];
        }
    }

    private function checkDatabaseService(): array
    {
        try {
            DB::connection()->getPdo();

            return [
                'name' => 'Database',
                'status' => 'healthy',
                'description' => 'Database connection active',
                'icon' => Heroicon::CircleStack,
                'color' => 'success',
            ];
        } catch (\Exception $e) {
            return [
                'name' => 'Database',
                'status' => 'error',
                'description' => 'Database connection failed',
                'icon' => Heroicon::CircleStack,
                'color' => 'danger',
            ];
        }
    }

    private function checkStorageService(): array
    {
        try {
            $disk = Storage::disk('local');
            $testFile = 'health_check_'.time().'.txt';
            $disk->put($testFile, 'test');
            $content = $disk->get($testFile);
            $disk->delete($testFile);

            return [
                'name' => 'Storage',
                'status' => $content === 'test' ? 'healthy' : 'warning',
                'description' => $content === 'test' ? 'File system read/write working' : 'Storage issues detected',
                'icon' => Heroicon::ServerStack,
                'color' => $content === 'test' ? 'success' : 'warning',
            ];
        } catch (\Exception $e) {
            return [
                'name' => 'Storage',
                'status' => 'error',
                'description' => 'Storage service unavailable',
                'icon' => Heroicon::ServerStack,
                'color' => 'danger',
            ];
        }
    }

    private function getQueueStatus(): array
    {
        return [
            'pending_jobs' => DB::table('jobs')->count(),
            'failed_jobs' => DB::table('failed_jobs')->count(),
            'processed_jobs' => DB::table('jobs')->where('available_at', '<=', now())->count(),
        ];
    }

    private function getStorageStatus(): array
    {
        $storagePath = storage_path();
        $totalSpace = disk_total_space($storagePath);
        $freeSpace = disk_free_space($storagePath);
        $usedSpace = $totalSpace - $freeSpace;

        return [
            'total' => $totalSpace,
            'used' => $usedSpace,
            'free' => $freeSpace,
            'usage_percent' => $totalSpace > 0 ? round(($usedSpace / $totalSpace) * 100, 1) : 0,
        ];
    }

    private function getDatabaseStatus(): array
    {
        try {
            // Test database connection
            DB::connection()->getPdo();

            // Get table count - compatible with SQLite and MySQL
            $tables = $this->getTableCount();

            return [
                'status' => 'connected',
                'tables_count' => $tables,
                'connection_name' => config('database.default'),
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'error',
                'error' => $e->getMessage(),
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
}
