<?php

namespace App\Filament\Resources\Contests\Pages;

use App\Filament\Resources\Contests\ContestResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListContests extends ListRecords
{
    protected static string $resource = ContestResource::class;

    /**
     * @return array<string, mixed>
     */
    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make(),
        ];
    }
}
