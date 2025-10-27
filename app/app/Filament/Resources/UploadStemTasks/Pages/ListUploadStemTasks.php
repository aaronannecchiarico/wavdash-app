<?php

namespace App\Filament\Resources\UploadStemTasks\Pages;

use App\Filament\Resources\UploadStemTasks\UploadStemTaskResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListUploadStemTasks extends ListRecords
{
    protected static string $resource = UploadStemTaskResource::class;

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
