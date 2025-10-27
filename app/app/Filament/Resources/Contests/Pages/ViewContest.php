<?php

namespace App\Filament\Resources\Contests\Pages;

use App\Filament\Resources\Contests\ContestResource;
use Filament\Actions\EditAction;
use Filament\Resources\Pages\ViewRecord;

class ViewContest extends ViewRecord
{
    protected static string $resource = ContestResource::class;

    /**
     * @return array<string, mixed>
     */
    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }
}
