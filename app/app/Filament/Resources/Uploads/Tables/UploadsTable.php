<?php

namespace App\Filament\Resources\Uploads\Tables;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Tables\Columns\IconColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;

class UploadsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->label('ID')
                    ->sortable(),
                TextColumn::make('title')
                    ->searchable()
                    ->sortable()
                    ->wrap(),
                TextColumn::make('user.name')
                    ->label('User')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('status')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'pending' => 'warning',
                        'processing' => 'info',
                        'ready' => 'success',
                        'failed' => 'danger',
                        default => 'gray',
                    }),
                TextColumn::make('size')
                    ->label('File Size')
                    ->formatStateUsing(fn (?int $state): string => $state ? number_format($state / 1024 / 1024, 2).' MB' : 'N/A'
                    )
                    ->sortable(),
                TextColumn::make('duration_seconds')
                    ->label('Duration')
                    ->formatStateUsing(fn (?int $state): string => $state ? gmdate('i:s', $state) : 'N/A'
                    )
                    ->sortable(),
                TextColumn::make('mime_type')
                    ->label('Type')
                    ->badge(),
                IconColumn::make('uses_r2_storage')
                    ->label('Cloud Storage')
                    ->boolean()
                    ->trueIcon('heroicon-o-cloud')
                    ->falseIcon('heroicon-o-server'),
                TextColumn::make('created_at')
                    ->label('Created')
                    ->dateTime()
                    ->sortable()
                    ->since(),
                TextColumn::make('genre')
                    ->searchable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('updated_at')
                    ->label('Updated')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                SelectFilter::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'processing' => 'Processing',
                        'ready' => 'Ready',
                        'failed' => 'Failed',
                    ])
                    ->multiple(),
                SelectFilter::make('uses_r2_storage')
                    ->label('Storage Type')
                    ->options([
                        true => 'Cloud Storage (R2)',
                        false => 'Local Storage',
                    ]),
                SelectFilter::make('user_id')
                    ->label('User')
                    ->relationship('user', 'name')
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
