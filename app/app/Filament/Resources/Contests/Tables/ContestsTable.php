<?php

namespace App\Filament\Resources\Contests\Tables;

use Carbon\Carbon;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Forms\Components\DatePicker;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\Filter;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;

class ContestsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->label('ID')
                    ->sortable(),
                TextColumn::make('name')
                    ->label('Contest Name')
                    ->searchable()
                    ->sortable()
                    ->wrap(),
                TextColumn::make('user.name')
                    ->label('Created By')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('genre')
                    ->searchable()
                    ->badge(),
                TextColumn::make('state')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'draft' => 'gray',
                        'open' => 'success',
                        'voting' => 'info',
                        'closed' => 'warning',
                        'completed' => 'success',
                        default => 'gray',
                    }),
                TextColumn::make('contestUsers_count')
                    ->label('Entries')
                    ->counts('contestUsers')
                    ->sortable(),
                TextColumn::make('votes_count')
                    ->label('Votes')
                    ->counts('votes')
                    ->sortable(),
                TextColumn::make('start_date')
                    ->label('Starts')
                    ->dateTime()
                    ->sortable()
                    ->since(),
                TextColumn::make('end_date')
                    ->label('Ends')
                    ->dateTime()
                    ->sortable()
                    ->since(),
                TextColumn::make('winner.name')
                    ->label('Winner')
                    ->searchable()
                    ->placeholder('TBD'),
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
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                SelectFilter::make('state')
                    ->options([
                        'draft' => 'Draft',
                        'open' => 'Open',
                        'voting' => 'Voting',
                        'closed' => 'Closed',
                        'completed' => 'Completed',
                    ])
                    ->multiple(),
                SelectFilter::make('genre')
                    ->options([
                        'hip-hop' => 'Hip-Hop',
                        'trap' => 'Trap',
                        'pop' => 'Pop',
                        'r&b' => 'R&B',
                        'electronic' => 'Electronic',
                        'rock' => 'Rock',
                        'jazz' => 'Jazz',
                        'classical' => 'Classical',
                        'reggae' => 'Reggae',
                        'country' => 'Country',
                        'other' => 'Other',
                    ])
                    ->multiple(),
                SelectFilter::make('user_id')
                    ->label('Created By')
                    ->relationship('user', 'name')
                    ->searchable(),
                Filter::make('date_range')
                    ->form([
                        DatePicker::make('start_date')->label('Start Date From'),
                        DatePicker::make('end_date')->label('End Date Until'),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        return $query
                            ->when(
                                $data['start_date'],
                                fn (Builder $query, $date): Builder => $query->whereDate('start_date', '>=', $date),
                            )
                            ->when(
                                $data['end_date'],
                                fn (Builder $query, $date): Builder => $query->whereDate('end_date', '<=', $date),
                            );
                    })
                    ->indicateUsing(function (array $data): array {
                        $indicators = [];
                        if ($data['start_date'] ?? null) {
                            $indicators['start_date'] = 'Start date from '.Carbon::parse($data['start_date'])->toFormattedDateString();
                        }
                        if ($data['end_date'] ?? null) {
                            $indicators['end_date'] = 'End date until '.Carbon::parse($data['end_date'])->toFormattedDateString();
                        }

                        return $indicators;
                    }),
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
