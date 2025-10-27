<?php

namespace App\Filament\Resources\UploadTempoTasks;

use App\Filament\Resources\UploadTempoTasks\Pages\CreateUploadTempoTask;
use App\Filament\Resources\UploadTempoTasks\Pages\EditUploadTempoTask;
use App\Filament\Resources\UploadTempoTasks\Pages\ListUploadTempoTasks;
use App\Filament\Resources\UploadTempoTasks\Pages\ViewUploadTempoTask;
use App\Filament\Resources\UploadTempoTasks\Schemas\UploadTempoTaskForm;
use App\Filament\Resources\UploadTempoTasks\Schemas\UploadTempoTaskInfolist;
use App\Filament\Resources\UploadTempoTasks\Tables\UploadTempoTasksTable;
use App\Models\UploadTempoTask;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;

class UploadTempoTaskResource extends Resource
{
    protected static ?string $model = UploadTempoTask::class;

    protected static ?string $navigationLabel = 'Tempo Tasks';

    protected static ?string $pluralModelLabel = 'tempo tasks';

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedClock;

    protected static ?int $navigationSort = 7;

    public static function form(Schema $schema): Schema
    {
        return UploadTempoTaskForm::configure($schema);
    }

    public static function infolist(Schema $schema): Schema
    {
        return UploadTempoTaskInfolist::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return UploadTempoTasksTable::configure($table);
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => ListUploadTempoTasks::route('/'),
            'create' => CreateUploadTempoTask::route('/create'),
            'view' => ViewUploadTempoTask::route('/{record}'),
            'edit' => EditUploadTempoTask::route('/{record}/edit'),
        ];
    }
}
