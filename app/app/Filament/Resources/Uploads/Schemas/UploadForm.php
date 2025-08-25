<?php

namespace App\Filament\Resources\Uploads\Schemas;

use Filament\Forms\Components\DateTimePicker;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Schemas\Schema;

class UploadForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Select::make('user_id')
                    ->relationship('user', 'name')
                    ->required(),
                TextInput::make('title')
                    ->required(),
                Textarea::make('description')
                    ->columnSpanFull(),
                TextInput::make('genre'),
                TextInput::make('filename')
                    ->required(),
                TextInput::make('path')
                    ->required(),
                TextInput::make('stream_path'),
                TextInput::make('mime_type')
                    ->required(),
                TextInput::make('size')
                    ->required()
                    ->numeric(),
                TextInput::make('status')
                    ->required()
                    ->default('pending'),
                TextInput::make('duration_seconds')
                    ->numeric(),
                TextInput::make('r2_upload_path'),
                Textarea::make('r2_stems_paths')
                    ->columnSpanFull(),
                TextInput::make('r2_analysis_path'),
                DateTimePicker::make('r2_uploaded_at'),
                Toggle::make('uses_r2_storage')
                    ->required(),
            ]);
    }
}
