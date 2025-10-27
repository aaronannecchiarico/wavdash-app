<?php

namespace App\Filament\Resources\UploadAnalysisTasks\Pages;

use App\Filament\Resources\UploadAnalysisTasks\UploadAnalysisTaskResource;
use Filament\Actions\DeleteAction;
use Filament\Actions\ViewAction;
use Filament\Resources\Pages\EditRecord;

class EditUploadAnalysisTask extends EditRecord
{
    protected static string $resource = UploadAnalysisTaskResource::class;

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
