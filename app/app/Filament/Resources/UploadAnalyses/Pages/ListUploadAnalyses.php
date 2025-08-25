<?php

namespace App\Filament\Resources\UploadAnalyses\Pages;

use App\Filament\Resources\UploadAnalyses\UploadAnalysisResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListUploadAnalyses extends ListRecords
{
    protected static string $resource = UploadAnalysisResource::class;

    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make(),
        ];
    }
}
