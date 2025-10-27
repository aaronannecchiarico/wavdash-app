<?php

namespace App\Filament\Resources\UploadAnalyses;

use App\Filament\Resources\UploadAnalyses\Pages\CreateUploadAnalysis;
use App\Filament\Resources\UploadAnalyses\Pages\EditUploadAnalysis;
use App\Filament\Resources\UploadAnalyses\Pages\ListUploadAnalyses;
use App\Filament\Resources\UploadAnalyses\Pages\ViewUploadAnalysis;
use App\Filament\Resources\UploadAnalyses\Schemas\UploadAnalysisForm;
use App\Filament\Resources\UploadAnalyses\Schemas\UploadAnalysisInfolist;
use App\Filament\Resources\UploadAnalyses\Tables\UploadAnalysesTable;
use App\Models\UploadAnalysis;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;

class UploadAnalysisResource extends Resource
{
    protected static ?string $model = UploadAnalysis::class;

    protected static ?string $navigationLabel = 'Audio Analysis';

    protected static ?string $pluralModelLabel = 'audio analyses';

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedChartBarSquare;

    protected static ?int $navigationSort = 4;

    public static function form(Schema $schema): Schema
    {
        return UploadAnalysisForm::configure($schema);
    }

    public static function infolist(Schema $schema): Schema
    {
        return UploadAnalysisInfolist::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return UploadAnalysesTable::configure($table);
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
            'index' => ListUploadAnalyses::route('/'),
            'create' => CreateUploadAnalysis::route('/create'),
            'view' => ViewUploadAnalysis::route('/{record}'),
            'edit' => EditUploadAnalysis::route('/{record}/edit'),
        ];
    }
}
