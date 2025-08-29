<?php

namespace App\Filament\Resources\UploadAnalysisTasks\Schemas;

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
                        TextEntry::make('status')
                            ->badge()
                            ->formatStateUsing(fn (string $state): string => ucfirst($state))
                            ->color(fn (string $state): string => match ($state) {
                                'pending' => 'warning',
                                'processing' => 'info',
                                'completed' => 'success',
                                'failed' => 'danger',
                                'deleted' => 'gray',
                                default => 'gray',
                            })
                            ->icon(fn (string $state): string => match ($state) {
                                'pending' => 'heroicon-o-clock',
                                'processing' => 'heroicon-o-arrow-path',
                                'completed' => 'heroicon-o-check-circle',
                                'failed' => 'heroicon-o-x-circle',
                                'deleted' => 'heroicon-o-trash',
                                default => 'heroicon-o-question-mark-circle',
                            })
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
