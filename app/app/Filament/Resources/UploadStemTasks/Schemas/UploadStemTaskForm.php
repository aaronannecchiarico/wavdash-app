<?php

namespace App\Filament\Resources\UploadStemTasks\Schemas;

use Filament\Forms\Components\DateTimePicker;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class UploadStemTaskForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Select::make('upload_id')
                    ->relationship('upload', 'title')
                    ->required(),
                TextInput::make('task_id')
                    ->required(),
                TextInput::make('status')
                    ->required()
                    ->default('pending'),
                Textarea::make('error_message')
                    ->columnSpanFull(),
                TextInput::make('progress')
                    ->required()
                    ->numeric()
                    ->default(0),
                DateTimePicker::make('submitted_at'),
                DateTimePicker::make('completed_at'),
            ]);
    }
}
