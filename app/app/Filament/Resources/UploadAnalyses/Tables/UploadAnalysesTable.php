<?php

namespace App\Filament\Resources\UploadAnalyses\Tables;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\Filter;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;

class UploadAnalysesTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->label('ID')
                    ->sortable(),
                TextColumn::make('upload.title')
                    ->label('Upload')
                    ->searchable()
                    ->sortable()
                    ->wrap(),
                TextColumn::make('upload.user.name')
                    ->label('Artist')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('musical_key')
                    ->label('Key')
                    ->badge()
                    ->sortable(),
                TextColumn::make('key_confidence')
                    ->label('Key Confidence')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state * 100, 1).'%' : 'N/A')
                    ->color(fn (?float $state): string => match (true) {
                        $state === null => 'gray',
                        $state > 0.8 => 'success',
                        $state > 0.6 => 'warning',
                        default => 'danger',
                    })
                    ->sortable(),
                TextColumn::make('bpm')
                    ->label('BPM')
                    ->badge()
                    ->color(fn (?int $state): string => match (true) {
                        $state === null => 'gray',
                        $state >= 140 => 'danger',  // Fast
                        $state >= 120 => 'warning', // Upbeat
                        $state >= 90 => 'success',  // Moderate
                        default => 'info',          // Slow
                    })
                    ->sortable(),
                TextColumn::make('loudness_db')
                    ->label('Loudness (dB)')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state, 1).' dB' : 'N/A')
                    ->color(fn (?float $state): string => match (true) {
                        $state === null => 'gray',
                        $state >= -6 => 'danger',   // Very Loud
                        $state >= -12 => 'warning', // Loud
                        $state >= -18 => 'success', // Moderate
                        default => 'info',          // Quiet
                    })
                    ->sortable(),
                TextColumn::make('dynamic_range_db')
                    ->label('Dynamic Range')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state, 1).' dB' : 'N/A')
                    ->color(fn (?float $state): string => match (true) {
                        $state === null => 'gray',
                        $state > 20 => 'success',   // High Range
                        $state >= 10 => 'warning', // Moderate
                        default => 'danger',        // Compressed
                    })
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('brightness')
                    ->label('Brightness')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state, 0).' Hz' : 'N/A')
                    ->color(fn (?float $state): string => match (true) {
                        $state === null => 'gray',
                        $state > 2000 => 'warning', // Bright
                        $state >= 1000 => 'success', // Balanced
                        default => 'info',          // Dark/Warm
                    })
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('timbral_complexity')
                    ->label('Complexity')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state, 2) : 'N/A')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('beat_regularity')
                    ->label('Beat Regularity')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state * 100, 1).'%' : 'N/A')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('key_changes')
                    ->label('Key Changes')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('analysis_duration')
                    ->label('Analysis Time')
                    ->formatStateUsing(fn (?float $state): string => $state ? number_format($state, 2).'s' : 'N/A')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('created_at')
                    ->label('Analyzed')
                    ->dateTime()
                    ->sortable()
                    ->since()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('updated_at')
                    ->label('Updated')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                SelectFilter::make('musical_key')
                    ->label('Musical Key')
                    ->options([
                        'C' => 'C Major', 'Cm' => 'C Minor',
                        'C#' => 'C# Major', 'C#m' => 'C# Minor',
                        'D' => 'D Major', 'Dm' => 'D Minor',
                        'D#' => 'D# Major', 'D#m' => 'D# Minor',
                        'E' => 'E Major', 'Em' => 'E Minor',
                        'F' => 'F Major', 'Fm' => 'F Minor',
                        'F#' => 'F# Major', 'F#m' => 'F# Minor',
                        'G' => 'G Major', 'Gm' => 'G Minor',
                        'G#' => 'G# Major', 'G#m' => 'G# Minor',
                        'A' => 'A Major', 'Am' => 'A Minor',
                        'A#' => 'A# Major', 'A#m' => 'A# Minor',
                        'B' => 'B Major', 'Bm' => 'B Minor',
                    ])
                    ->multiple(),
                Filter::make('bpm_range')
                    ->label('BPM Range')
                    ->form([
                        \Filament\Forms\Components\Select::make('bpm_category')
                            ->label('BPM Category')
                            ->options([
                                'slow' => 'Slow (< 90 BPM)',
                                'moderate' => 'Moderate (90-119 BPM)',
                                'upbeat' => 'Upbeat (120-139 BPM)',
                                'fast' => 'Fast (140+ BPM)',
                            ])
                            ->multiple(),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        if (empty($data['bpm_category'])) {
                            return $query;
                        }

                        return $query->where(function (Builder $query) use ($data) {
                            foreach ($data['bpm_category'] as $category) {
                                match ($category) {
                                    'slow' => $query->orWhere('bpm', '<', 90),
                                    'moderate' => $query->orWhere(fn ($q) => $q->whereBetween('bpm', [90, 119])),
                                    'upbeat' => $query->orWhere(fn ($q) => $q->whereBetween('bpm', [120, 139])),
                                    'fast' => $query->orWhere('bpm', '>=', 140),
                                    default => null, // Ignore unknown categories
                                };
                            }
                        });
                    }),
                Filter::make('loudness_range')
                    ->label('Loudness Category')
                    ->form([
                        \Filament\Forms\Components\Select::make('loudness_category')
                            ->label('Loudness')
                            ->options([
                                'quiet' => 'Quiet (< -18 dB)',
                                'moderate' => 'Moderate (-18 to -12 dB)',
                                'loud' => 'Loud (-12 to -6 dB)',
                                'very_loud' => 'Very Loud (> -6 dB)',
                            ])
                            ->multiple(),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        if (empty($data['loudness_category'])) {
                            return $query;
                        }

                        return $query->where(function (Builder $query) use ($data) {
                            foreach ($data['loudness_category'] as $category) {
                                match ($category) {
                                    'quiet' => $query->orWhere('loudness_db', '<', -18),
                                    'moderate' => $query->orWhere(fn ($q) => $q->whereBetween('loudness_db', [-18, -12])),
                                    'loud' => $query->orWhere(fn ($q) => $q->whereBetween('loudness_db', [-12, -6])),
                                    'very_loud' => $query->orWhere('loudness_db', '>', -6),
                                    default => null, // Ignore unknown categories
                                };
                            }
                        });
                    }),
                SelectFilter::make('key_reliability')
                    ->label('Key Detection Quality')
                    ->options([
                        'reliable' => 'Reliable (>80%)',
                        'moderate' => 'Moderate (60-80%)',
                        'unreliable' => 'Unreliable (<60%)',
                    ])
                    ->query(function (Builder $query, $state): Builder {
                        return match ($state) {
                            'reliable' => $query->where('key_confidence', '>', 0.8),
                            'moderate' => $query->whereBetween('key_confidence', [0.6, 0.8]),
                            'unreliable' => $query->where('key_confidence', '<', 0.6),
                            default => $query,
                        };
                    }),
                SelectFilter::make('upload.user_id')
                    ->label('Artist')
                    ->relationship('upload.user', 'name')
                    ->searchable(),
            ])
            ->recordActions([
                ViewAction::make(),
                EditAction::make(),
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}
