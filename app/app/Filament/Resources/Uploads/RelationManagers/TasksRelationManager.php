<?php

namespace App\Filament\Resources\Uploads\RelationManagers;

use App\Models\UploadAnalysisTask;
use App\Models\UploadStemTask;
use App\Models\UploadTempoTask;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Schemas\Components\Select;
use Filament\Schemas\Components\TextInput;
use Filament\Schemas\Schema;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;

class TasksRelationManager extends RelationManager
{
    protected static string $relationship = 'analysisTask';

    protected static ?string $recordTitleAttribute = 'task_id';

    protected static ?string $title = 'Processing Tasks';

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('task_id')
                    ->label('Task ID')
                    ->required()
                    ->maxLength(255),
                Select::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'processing' => 'Processing',
                        'completed' => 'Completed',
                        'failed' => 'Failed',
                        'deleted' => 'Deleted',
                    ])
                    ->required(),
                TextInput::make('progress')
                    ->numeric()
                    ->minValue(0)
                    ->maxValue(100)
                    ->default(0),
                TextInput::make('error_message')
                    ->maxLength(1000),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->heading('All Processing Tasks')
            ->description('View all processing tasks (Analysis, Stem Separation, and Tempo Processing) for this upload.')
            ->columns([
                TextColumn::make('task_type')
                    ->label('Type')
                    ->getStateUsing(function ($record) {
                        return match (get_class($record)) {
                            UploadAnalysisTask::class => 'Analysis',
                            UploadStemTask::class => 'Stem Separation',
                            UploadTempoTask::class => 'Tempo Processing',
                            default => 'Unknown',
                        };
                    })
                    ->badge()
                    ->color(function ($state) {
                        return match ($state) {
                            'Analysis' => 'info',
                            'Stem Separation' => 'warning',
                            'Tempo Processing' => 'success',
                            default => 'gray',
                        };
                    })
                    ->sortable(),
                TextColumn::make('task_id')
                    ->label('Task ID')
                    ->copyable()
                    ->limit(20),
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
                TextColumn::make('submitted_at')
                    ->label('Submitted')
                    ->dateTime()
                    ->since()
                    ->sortable(),
                TextColumn::make('completed_at')
                    ->label('Completed')
                    ->dateTime()
                    ->since()
                    ->placeholder('In Progress'),
            ])
            ->filters([
                SelectFilter::make('task_type')
                    ->label('Task Type')
                    ->options([
                        UploadAnalysisTask::class => 'Analysis',
                        UploadStemTask::class => 'Stem Separation',
                        UploadTempoTask::class => 'Tempo Processing',
                    ])
                    ->query(function (Builder $query, $state) {
                        if (! $state['value']) {
                            return $query;
                        }

                        // This would need custom implementation to work properly
                        return $query;
                    }),
                SelectFilter::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'processing' => 'Processing',
                        'completed' => 'Completed',
                        'failed' => 'Failed',
                        'deleted' => 'Deleted',
                    ])
                    ->multiple(),
            ])
            ->defaultSort('submitted_at', 'desc');
    }
}
