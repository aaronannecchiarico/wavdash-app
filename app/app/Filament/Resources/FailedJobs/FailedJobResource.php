<?php

namespace App\Filament\Resources\FailedJobs;

use App\Filament\Resources\FailedJobs\Pages\ManageFailedJobs;
use App\Filament\Resources\FailedJobs\Tables\FailedJobsTable;
use App\Models\FailedJob;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;

class FailedJobResource extends Resource
{
    protected static ?string $model = FailedJob::class;

    protected static ?string $navigationLabel = 'Failed Jobs';

    protected static ?string $pluralModelLabel = 'failed jobs';

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedExclamationTriangle;

    protected static ?int $navigationSort = 10;

    public static function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                // Failed jobs are typically read-only, no form needed
            ]);
    }

    public static function table(Table $table): Table
    {
        return FailedJobsTable::configure($table);
    }

    public static function getPages(): array
    {
        return [
            'index' => ManageFailedJobs::route('/'),
        ];
    }

    public static function canCreate(): bool
    {
        return false; // Failed jobs cannot be created manually
    }

    public static function canEdit($record): bool
    {
        return false; // Failed jobs are read-only
    }
}
