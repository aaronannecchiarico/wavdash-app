<?php

namespace App\Filament\Resources\UploadAnalysisTasks\Pages;

use App\Filament\Resources\UploadAnalysisTasks\UploadAnalysisTaskResource;
use Filament\Actions\EditAction;
use Filament\Resources\Pages\ViewRecord;

class ViewUploadAnalysisTask extends ViewRecord
{
    protected static string $resource = UploadAnalysisTaskResource::class;

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }
}
