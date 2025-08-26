<?php

namespace App\Filament\Resources\Uploads\Schemas;

use App\Filament\Infolists\Components\AudioPlayerEntry;
use App\Filament\Infolists\Components\FileSizeEntry;
use App\Filament\Infolists\Components\ProcessingStatusEntry;
use Filament\Infolists\Components\IconEntry;
use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;

class UploadInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make('Audio Player')
                    ->schema([
                        AudioPlayerEntry::make('id')
                            ->columnSpanFull(),
                    ])
                    ->collapsible(),

                Section::make('Basic Information')
                    ->schema([
                        TextEntry::make('user.name')
                            ->label('Uploaded by'),
                        TextEntry::make('title')
                            ->weight('bold'),
                        TextEntry::make('genre'),
                        TextEntry::make('filename'),
                        TextEntry::make('mime_type')
                            ->label('File Type'),
                        FileSizeEntry::make('size')
                            ->label('File Size'),
                        TextEntry::make('duration_seconds')
                            ->formatStateUsing(fn (?int $state): string => $state ? gmdate('H:i:s', $state) : 'Unknown'
                            )
                            ->label('Duration'),
                    ])
                    ->columns(2),

                Section::make('Processing Status')
                    ->schema([
                        ProcessingStatusEntry::make('status')
                            ->columnSpanFull(),
                    ])
                    ->collapsible(),

                Section::make('Storage Information')
                    ->schema([
                        TextEntry::make('path')
                            ->copyable()
                            ->tooltip('Original file path'),
                        TextEntry::make('stream_path')
                            ->copyable()
                            ->tooltip('Streaming file path'),
                        TextEntry::make('r2_upload_path')
                            ->copyable()
                            ->tooltip('R2 bucket path')
                            ->visible(fn ($record) => $record->uses_r2_storage),
                        TextEntry::make('r2_analysis_path')
                            ->copyable()
                            ->tooltip('R2 analysis results path')
                            ->visible(fn ($record) => $record->uses_r2_storage && $record->r2_analysis_path),
                        IconEntry::make('uses_r2_storage')
                            ->boolean()
                            ->label('Uses Cloud Storage'),
                        TextEntry::make('r2_uploaded_at')
                            ->dateTime()
                            ->since()
                            ->visible(fn ($record) => $record->uses_r2_storage && $record->r2_uploaded_at),
                    ])
                    ->columns(2)
                    ->collapsible(),

                Section::make('Timestamps')
                    ->schema([
                        TextEntry::make('created_at')
                            ->dateTime()
                            ->since(),
                        TextEntry::make('updated_at')
                            ->dateTime()
                            ->since(),
                    ])
                    ->columns(2)
                    ->collapsed(),
            ]);
    }
}
