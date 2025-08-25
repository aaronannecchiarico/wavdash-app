<?php

namespace App\Filament\Resources\Uploads\Schemas;

use Filament\Infolists\Components\IconEntry;
use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Schema;

class UploadInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextEntry::make('user.name'),
                TextEntry::make('title'),
                TextEntry::make('genre'),
                TextEntry::make('filename'),
                TextEntry::make('path'),
                TextEntry::make('stream_path'),
                TextEntry::make('mime_type'),
                TextEntry::make('size')
                    ->numeric(),
                TextEntry::make('status'),
                TextEntry::make('duration_seconds')
                    ->numeric(),
                TextEntry::make('created_at')
                    ->dateTime(),
                TextEntry::make('updated_at')
                    ->dateTime(),
                TextEntry::make('r2_upload_path'),
                TextEntry::make('r2_analysis_path'),
                TextEntry::make('r2_uploaded_at')
                    ->dateTime(),
                IconEntry::make('uses_r2_storage')
                    ->boolean(),
            ]);
    }
}
