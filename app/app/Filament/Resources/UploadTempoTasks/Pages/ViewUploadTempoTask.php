<?php

namespace App\Filament\Resources\UploadTempoTasks\Pages;

use App\Filament\Resources\UploadTempoTasks\UploadTempoTaskResource;
use Filament\Actions\EditAction;
use Filament\Resources\Pages\ViewRecord;

class ViewUploadTempoTask extends ViewRecord
{
    protected static string $resource = UploadTempoTaskResource::class;

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }
}
