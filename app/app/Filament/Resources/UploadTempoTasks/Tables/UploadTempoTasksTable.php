<?php

namespace App\Filament\Resources\UploadTempoTasks\Tables;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;

class UploadTempoTasksTable
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
                    ->label('User')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('task_id')
                    ->label('Task ID')
                    ->searchable()
                    ->copyable(),
                TextColumn::make('status')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'pending' => 'warning',
                        'processing' => 'info',
                        'completed' => 'success',
                        'failed' => 'danger',
                        'deleted' => 'gray',
                        default => 'gray',
                    })
                    ->sortable(),
                TextColumn::make('progress')
                    ->label('Progress')
                    ->formatStateUsing(fn (?int $state): string => $state ? $state.'%' : 'N/A')
                    ->color(fn (?int $state): string => match (true) {
                        $state === null => 'gray',
                        $state >= 100 => 'success',
                        $state >= 75 => 'info',
                        $state >= 50 => 'warning',
                        default => 'danger',
                    })
                    ->sortable(),
                TextColumn::make('processing_options')
                    ->label('Options')
                    ->formatStateUsing(fn (?array $state): string => $state ? implode(', ', array_keys($state)) : 'Default')
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('submitted_at')
                    ->label('Submitted')
                    ->dateTime()
                    ->sortable()
                    ->since(),
                TextColumn::make('completed_at')
                    ->label('Completed')
                    ->dateTime()
                    ->sortable()
                    ->since()
                    ->placeholder('In Progress'),
                TextColumn::make('error_message')
                    ->label('Error')
                    ->limit(50)
                    ->tooltip(fn (?string $state): ?string => $state)
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('created_at')
                    ->label('Created')
                    ->dateTime()
                    ->sortable()
                    ->since()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('updated_at')
                    ->label('Updated')
                    ->dateTime()
                    ->sortable()
                    ->since()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                SelectFilter::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'processing' => 'Processing',
                        'completed' => 'Completed',
                        'failed' => 'Failed',
                        'deleted' => 'Deleted',
                    ])
                    ->multiple(),
                SelectFilter::make('upload.user_id')
                    ->label('User')
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
