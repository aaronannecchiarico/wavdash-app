<?php

namespace App\Filament\Resources\UploadStemTasks\Pages;

use App\Filament\Resources\UploadStemTasks\UploadStemTaskResource;
use Filament\Actions\DeleteAction;
use Filament\Actions\ViewAction;
use Filament\Resources\Pages\EditRecord;

class EditUploadStemTask extends EditRecord
{
    protected static string $resource = UploadStemTaskResource::class;

    protected function getHeaderActions(): array
    {
        return [
            ViewAction::make(),
            DeleteAction::make(),
        ];
    }
}
