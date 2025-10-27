<?php

namespace App\Filament\Resources\Uploads\RelationManagers;

use Filament\Resources\RelationManagers\RelationManager;
use Filament\Schemas\Components\TextInput;
use Filament\Schemas\Schema;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;

class AnalysisRelationManager extends RelationManager
{
    protected static string $relationship = 'analysis';

    protected static ?string $recordTitleAttribute = 'musical_key';

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('musical_key')
                    ->required()
                    ->maxLength(10),
                TextInput::make('bpm')
                    ->numeric()
                    ->minValue(1)
                    ->maxValue(300),
                TextInput::make('key_confidence')
                    ->numeric()
                    ->step(0.01)
                    ->minValue(0)
                    ->maxValue(1),
                TextInput::make('loudness_db')
                    ->numeric()
                    ->step(0.1),
                TextInput::make('brightness')
                    ->numeric(),
                TextInput::make('analysis_duration')
                    ->numeric()
                    ->step(0.01),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('musical_key')
                    ->label('Key')
                    ->badge()
                    ->sortable(),
                TextColumn::make('bpm')
                    ->label('BPM')
                    ->sortable(),
                TextColumn::make('key_confidence')
                    ->label('Confidence')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state * 100, 1).'%' : 'N/A')
                    ->sortable(),
                TextColumn::make('loudness_db')
                    ->label('Loudness')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state, 1).' dB' : 'N/A')
                    ->sortable(),
                TextColumn::make('created_at')
                    ->label('Analyzed')
                    ->dateTime()
                    ->since()
                    ->sortable(),
            ])
            ->defaultSort('created_at', 'desc');
    }
}
