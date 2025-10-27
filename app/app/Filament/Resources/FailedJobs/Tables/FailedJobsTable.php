<?php

namespace App\Filament\Resources\FailedJobs\Tables;

use Filament\Actions\DeleteAction;
use Filament\Actions\ViewAction;
use Filament\Infolists\Components\CodeEntry;
use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Section;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;

class FailedJobsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->label('ID')
                    ->sortable(),
                TextColumn::make('uuid')
                    ->label('UUID')
                    ->searchable()
                    ->copyable()
                    ->copyMessage('UUID copied!')
                    ->limit(20),
                TextColumn::make('job_class')
                    ->label('Job Class')
                    ->searchable()
                    ->wrap()
                    ->formatStateUsing(fn (?string $state): string => $state ? class_basename($state) : 'Unknown Job'
                    ),
                TextColumn::make('queue')
                    ->label('Queue')
                    ->badge()
                    ->searchable()
                    ->sortable(),
                TextColumn::make('connection')
                    ->label('Connection')
                    ->badge()
                    ->color('info')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('short_exception')
                    ->label('Exception')
                    ->limit(50)
                    ->tooltip(function ($record): ?string {
                        return $record->exception;
                    })
                    ->wrap(),
                TextColumn::make('failed_at')
                    ->label('Failed At')
                    ->dateTime()
                    ->sortable()
                    ->since()
                    ->description(fn ($record): string => $record->failed_at?->format('M j, Y g:i A')),
            ])
            ->filters([
                SelectFilter::make('queue')
                    ->options([
                        'default' => 'Default',
                        'high' => 'High Priority',
                        'low' => 'Low Priority',
                    ])
                    ->multiple(),
                SelectFilter::make('connection')
                    ->options([
                        'database' => 'Database',
                        'redis' => 'Redis',
                        'sync' => 'Sync',
                    ])
                    ->multiple(),
            ])
            ->recordActions([
                ViewAction::make()
                    ->modalHeading('Failed Job Details')
                    ->modalWidth('6xl')
                    ->schema([
                        Section::make('Job Information')
                            ->schema([
                                Grid::make(2)
                                    ->schema([
                                        TextEntry::make('uuid')
                                            ->label('UUID')
                                            ->copyable()
                                            ->copyMessage('UUID copied!')
                                            ->fontFamily('mono'),
                                        TextEntry::make('job_class')
                                            ->label('Job Class')
                                            ->formatStateUsing(fn (?string $state): string => $state ? class_basename($state) : 'Unknown Job'
                                            ),
                                        TextEntry::make('queue')
                                            ->label('Queue')
                                            ->badge(),
                                        TextEntry::make('connection')
                                            ->label('Connection')
                                            ->badge()
                                            ->color('info'),
                                        TextEntry::make('failed_at')
                                            ->label('Failed At')
                                            ->dateTime()
                                            ->since()
                                            ->columnSpanFull(),
                                    ]),
                            ]),
                        Section::make('Job Payload')
                            ->schema([
                                CodeEntry::make('payload')
                                    ->label('')
                                    ->formatStateUsing(function ($record): string {
                                        if (! $record->payload || ! is_array($record->payload)) {
                                            return 'No payload data available';
                                        }

                                        return json_encode($record->payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
                                    })
                                    ->copyable()
                                    ->copyMessage('Payload copied!')
                                    ->copyMessageDuration(2000),
                            ])
                            ->visible(fn ($record) => $record->payload && is_array($record->payload))
                            ->collapsible()
                            ->collapsed(),
                        Section::make('Exception Details')
                            ->schema([
                                TextEntry::make('exception')
                                    ->label('')
                                    ->formatStateUsing(function (string $state): \Illuminate\Support\HtmlString {
                                        // Add proper line breaks for better readability
                                        $formatted = str_replace([
                                            ' in ',
                                            ' on line ',
                                            'Stack trace:',
                                            '#0 ',
                                            '#1 ',
                                            '#2 ',
                                            '#3 ',
                                            '#4 ',
                                            '#5 ',
                                            '#6 ',
                                            '#7 ',
                                            '#8 ',
                                            '#9 ',
                                        ], [
                                            '<br>in ',
                                            '<br>on line ',
                                            '<br><br><strong>Stack trace:</strong>',
                                            '<br>#0 ',
                                            '<br>#1 ',
                                            '<br>#2 ',
                                            '<br>#3 ',
                                            '<br>#4 ',
                                            '<br>#5 ',
                                            '<br>#6 ',
                                            '<br>#7 ',
                                            '<br>#8 ',
                                            '<br>#9 ',
                                        ], htmlspecialchars($state));

                                        return new \Illuminate\Support\HtmlString($formatted);
                                    })
                                    ->fontFamily('mono')
                                    ->copyable()
                                    ->copyMessage('Exception copied!')
                                    ->copyMessageDuration(2000)
                                    ->color('danger'),
                            ])
                            ->visible(fn ($record) => ! empty($record->exception))
                            ->collapsible()
                            ->collapsed(false),
                    ])
                    ->modalSubmitAction(false)
                    ->modalCancelActionLabel('Close'),
                DeleteAction::make()
                    ->requiresConfirmation()
                    ->modalHeading('Delete Failed Job')
                    ->modalDescription('Are you sure you want to delete this failed job? This action cannot be undone.'),
            ])
            ->toolbarActions([
                // Bulk actions removed to prevent policy issues
            ])
            ->defaultSort('failed_at', 'desc')
            ->striped()
            ->paginated([10, 25, 50, 100]);
    }
}
