<?php

namespace App\Filament\Resources\UploadTempoTasks\Pages;

use App\Filament\Resources\UploadTempoTasks\UploadTempoTaskResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListUploadTempoTasks extends ListRecords
{
    protected static string $resource = UploadTempoTaskResource::class;

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
