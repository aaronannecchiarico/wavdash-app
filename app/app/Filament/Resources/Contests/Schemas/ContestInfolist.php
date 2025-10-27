<?php

namespace App\Filament\Resources\Contests\Schemas;

use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Schema;

class ContestInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextEntry::make('user.name'),
                TextEntry::make('name'),
                TextEntry::make('genre'),
                TextEntry::make('state'),
                TextEntry::make('start_date')
                    ->dateTime(),
                TextEntry::make('end_date')
                    ->dateTime(),
                TextEntry::make('winner.name'),
                TextEntry::make('created_at')
                    ->dateTime(),
                TextEntry::make('updated_at')
                    ->dateTime(),
            ]);
    }
}
