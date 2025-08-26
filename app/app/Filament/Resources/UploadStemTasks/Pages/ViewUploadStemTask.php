<?php

namespace App\Filament\Resources\UploadStemTasks\Pages;

use App\Filament\Resources\UploadStemTasks\UploadStemTaskResource;
use Filament\Actions\EditAction;
use Filament\Resources\Pages\ViewRecord;

class ViewUploadStemTask extends ViewRecord
{
    protected static string $resource = UploadStemTaskResource::class;

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }
}
