<?php

namespace App\Filament\Resources\UploadAnalyses\Schemas;

use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Schema;

class UploadAnalysisInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextEntry::make('upload.title'),
                TextEntry::make('musical_key'),
                TextEntry::make('key_confidence')
                    ->numeric(),
                TextEntry::make('bpm')
                    ->numeric(),
                TextEntry::make('beat_regularity')
                    ->numeric(),
                TextEntry::make('loudness_db')
                    ->numeric(),
                TextEntry::make('dynamic_range_db')
                    ->numeric(),
                TextEntry::make('brightness')
                    ->numeric(),
                TextEntry::make('timbral_complexity')
                    ->numeric(),
                TextEntry::make('analysis_duration')
                    ->numeric(),
                TextEntry::make('chunk_count')
                    ->numeric(),
                TextEntry::make('key_changes')
                    ->numeric(),
                TextEntry::make('created_at')
                    ->dateTime(),
                TextEntry::make('updated_at')
                    ->dateTime(),
            ]);
    }
}
