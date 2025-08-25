<?php

namespace App\Filament\Resources\UploadAnalyses\Pages;

use App\Filament\Resources\UploadAnalyses\UploadAnalysisResource;
use Filament\Actions\EditAction;
use Filament\Resources\Pages\ViewRecord;

class ViewUploadAnalysis extends ViewRecord
{
    protected static string $resource = UploadAnalysisResource::class;

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }
}
