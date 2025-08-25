<?php

namespace App\Filament\Resources\Contests;

use App\Filament\Resources\Contests\Pages\CreateContest;
use App\Filament\Resources\Contests\Pages\EditContest;
use App\Filament\Resources\Contests\Pages\ListContests;
use App\Filament\Resources\Contests\Pages\ViewContest;
use App\Filament\Resources\Contests\Schemas\ContestForm;
use App\Filament\Resources\Contests\Schemas\ContestInfolist;
use App\Filament\Resources\Contests\Tables\ContestsTable;
use App\Models\Contest;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;

class ContestResource extends Resource
{
    protected static ?string $model = Contest::class;

    protected static ?string $navigationLabel = 'Contests';

    protected static ?string $pluralModelLabel = 'contests';

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedTrophy;

    protected static ?int $navigationSort = 3;

    public static function form(Schema $schema): Schema
    {
        return ContestForm::configure($schema);
    }

    public static function infolist(Schema $schema): Schema
    {
        return ContestInfolist::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return ContestsTable::configure($table);
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
            'index' => ListContests::route('/'),
            'create' => CreateContest::route('/create'),
            'view' => ViewContest::route('/{record}'),
            'edit' => EditContest::route('/{record}/edit'),
        ];
    }
}
