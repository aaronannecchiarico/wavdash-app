<?php

namespace App\Filament\Resources\UploadAnalyses\Pages;

use App\Filament\Resources\UploadAnalyses\UploadAnalysisResource;
use Filament\Actions\DeleteAction;
use Filament\Actions\ViewAction;
use Filament\Resources\Pages\EditRecord;

class EditUploadAnalysis extends EditRecord
{
    protected static string $resource = UploadAnalysisResource::class;

    protected function getHeaderActions(): array
    {
        return [
            ViewAction::make(),
            DeleteAction::make(),
        ];
    }
}
