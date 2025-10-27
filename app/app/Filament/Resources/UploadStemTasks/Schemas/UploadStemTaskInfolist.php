<?php

namespace App\Filament\Resources\UploadStemTasks\Schemas;

use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Schema;

class UploadStemTaskInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextEntry::make('upload.title'),
                TextEntry::make('task_id'),
                TextEntry::make('status'),
                TextEntry::make('progress')
                    ->numeric(),
                TextEntry::make('submitted_at')
                    ->dateTime(),
                TextEntry::make('completed_at')
                    ->dateTime(),
                TextEntry::make('created_at')
                    ->dateTime(),
                TextEntry::make('updated_at')
                    ->dateTime(),
            ]);
    }
}
