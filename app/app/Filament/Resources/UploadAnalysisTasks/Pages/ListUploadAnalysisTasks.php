<?php

namespace App\Filament\Resources\UploadAnalysisTasks\Pages;

use App\Filament\Resources\UploadAnalysisTasks\UploadAnalysisTaskResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListUploadAnalysisTasks extends ListRecords
{
    protected static string $resource = UploadAnalysisTaskResource::class;

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
