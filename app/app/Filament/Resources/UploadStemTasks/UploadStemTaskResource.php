<?php

namespace App\Filament\Resources\UploadStemTasks;

use App\Filament\Resources\UploadStemTasks\Pages\CreateUploadStemTask;
use App\Filament\Resources\UploadStemTasks\Pages\EditUploadStemTask;
use App\Filament\Resources\UploadStemTasks\Pages\ListUploadStemTasks;
use App\Filament\Resources\UploadStemTasks\Pages\ViewUploadStemTask;
use App\Filament\Resources\UploadStemTasks\Schemas\UploadStemTaskForm;
use App\Filament\Resources\UploadStemTasks\Schemas\UploadStemTaskInfolist;
use App\Filament\Resources\UploadStemTasks\Tables\UploadStemTasksTable;
use App\Models\UploadStemTask;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;

class UploadStemTaskResource extends Resource
{
    protected static ?string $model = UploadStemTask::class;

    protected static ?string $navigationLabel = 'Stem Tasks';

    protected static ?string $pluralModelLabel = 'stem tasks';

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedScissors;

    protected static ?int $navigationSort = 6;

    public static function form(Schema $schema): Schema
    {
        return UploadStemTaskForm::configure($schema);
    }

    public static function infolist(Schema $schema): Schema
    {
        return UploadStemTaskInfolist::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return UploadStemTasksTable::configure($table);
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
            'index' => ListUploadStemTasks::route('/'),
            'create' => CreateUploadStemTask::route('/create'),
            'view' => ViewUploadStemTask::route('/{record}'),
            'edit' => EditUploadStemTask::route('/{record}/edit'),
        ];
    }
}
