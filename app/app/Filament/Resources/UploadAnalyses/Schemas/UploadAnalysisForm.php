<?php

namespace App\Filament\Resources\UploadAnalyses\Schemas;

use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class UploadAnalysisForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Select::make('upload_id')
                    ->relationship('upload', 'title')
                    ->required(),
                TextInput::make('musical_key'),
                TextInput::make('key_confidence')
                    ->numeric(),
                TextInput::make('bpm')
                    ->numeric(),
                TextInput::make('beat_regularity')
                    ->numeric(),
                TextInput::make('loudness_db')
                    ->numeric(),
                TextInput::make('dynamic_range_db')
                    ->numeric(),
                TextInput::make('brightness')
                    ->numeric(),
                TextInput::make('timbral_complexity')
                    ->numeric(),
                TextInput::make('analysis_duration')
                    ->numeric(),
                TextInput::make('chunk_count')
                    ->numeric(),
                TextInput::make('key_changes')
                    ->required()
                    ->numeric()
                    ->default(1),
            ]);
    }
}
