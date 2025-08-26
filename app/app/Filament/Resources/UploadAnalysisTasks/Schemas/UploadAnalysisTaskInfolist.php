<?php

namespace App\Filament\Resources\UploadAnalysisTasks\Schemas;

use App\Filament\Infolists\Components\ProcessingStatusEntry;
use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;

class UploadAnalysisTaskInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make('Task Information')
                    ->schema([
                        TextEntry::make('upload.title')
                            ->label('Upload')
                            ->weight('bold'),
                        TextEntry::make('task_id')
                            ->copyable(),
                        ProcessingStatusEntry::make('status')
                            ->columnSpanFull(),
                    ]),

                Section::make('Timestamps')
                    ->schema([
                        TextEntry::make('submitted_at')
                            ->dateTime()
                            ->since(),
                        TextEntry::make('completed_at')
                            ->dateTime()
                            ->since()
                            ->placeholder('Not completed'),
                        TextEntry::make('created_at')
                            ->dateTime()
                            ->since(),
                        TextEntry::make('updated_at')
                            ->dateTime()
                            ->since(),
                    ])
                    ->columns(2)
                    ->collapsible(),
            ]);
    }
}
