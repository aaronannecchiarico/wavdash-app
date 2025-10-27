<?php

namespace App\Filament\Resources\UploadTempoTasks\Pages;

use App\Filament\Resources\UploadTempoTasks\UploadTempoTaskResource;
use Filament\Actions\DeleteAction;
use Filament\Actions\ViewAction;
use Filament\Resources\Pages\EditRecord;

class EditUploadTempoTask extends EditRecord
{
    protected static string $resource = UploadTempoTaskResource::class;

    /**
     * @return array<string, mixed>
     */
    protected function getHeaderActions(): array
    {
        return [
            ViewAction::make(),
            DeleteAction::make(),
        ];
    }
}
