<?php

namespace App\Filament\Resources\UploadAnalysisTasks;

use App\Filament\Resources\UploadAnalysisTasks\Pages\CreateUploadAnalysisTask;
use App\Filament\Resources\UploadAnalysisTasks\Pages\EditUploadAnalysisTask;
use App\Filament\Resources\UploadAnalysisTasks\Pages\ListUploadAnalysisTasks;
use App\Filament\Resources\UploadAnalysisTasks\Pages\ViewUploadAnalysisTask;
use App\Filament\Resources\UploadAnalysisTasks\Schemas\UploadAnalysisTaskForm;
use App\Filament\Resources\UploadAnalysisTasks\Schemas\UploadAnalysisTaskInfolist;
use App\Filament\Resources\UploadAnalysisTasks\Tables\UploadAnalysisTasksTable;
use App\Models\UploadAnalysisTask;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;

class UploadAnalysisTaskResource extends Resource
{
    protected static ?string $model = UploadAnalysisTask::class;

    protected static ?string $navigationLabel = 'Analysis Tasks';

    protected static ?string $pluralModelLabel = 'analysis tasks';

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedCog6Tooth;

    protected static ?int $navigationSort = 5;

    public static function form(Schema $schema): Schema
    {
        return UploadAnalysisTaskForm::configure($schema);
    }

    public static function infolist(Schema $schema): Schema
    {
        return UploadAnalysisTaskInfolist::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return UploadAnalysisTasksTable::configure($table);
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
            'index' => ListUploadAnalysisTasks::route('/'),
            'create' => CreateUploadAnalysisTask::route('/create'),
            'view' => ViewUploadAnalysisTask::route('/{record}'),
            'edit' => EditUploadAnalysisTask::route('/{record}/edit'),
        ];
    }
}
