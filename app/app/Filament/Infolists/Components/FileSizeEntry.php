<?php

namespace App\Filament\Infolists\Components;

use Filament\Infolists\Components\Entry;

class FileSizeEntry extends Entry
{
    protected string $view = 'filament.infolists.components.file-size-entry';
    
    public static function formatBytes(int $bytes, int $precision = 2): string
    {
        if ($bytes === 0) {
            return '0 B';
        }

        $units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];

        for ($i = 0; $bytes > 1024 && $i < count($units) - 1; $i++) {
            $bytes /= 1024;
        }

        return round($bytes, $precision).' '.$units[$i];
    }
    
    public function getFormattedSize(): string
    {
        $size = $this->getState();
        
        if (!is_numeric($size)) {
            return 'Unknown';
        }
        
        return $this::formatBytes((int) $size);
    }
}
