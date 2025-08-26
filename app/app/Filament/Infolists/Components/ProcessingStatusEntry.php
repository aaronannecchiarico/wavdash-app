<?php

namespace App\Filament\Infolists\Components;

use Filament\Infolists\Components\Entry;

class ProcessingStatusEntry extends Entry
{
    protected string $view = 'filament.infolists.components.processing-status-entry';
    
    public static function calculateTimeRemaining($record): ?int
    {
        if (! $record || ! $record->submitted_at || $record->status !== 'processing') {
            return null;
        }

        $progress = $record->progress ?? 0;
        if ($progress <= 0) {
            return null;
        }

        $elapsedSeconds = now()->diffInSeconds($record->submitted_at);
        $totalEstimatedSeconds = ($elapsedSeconds / $progress) * 100;

        return max(0, (int) ($totalEstimatedSeconds - $elapsedSeconds));
    }

    public static function getStatusColor(string $status): string
    {
        return match ($status) {
            'pending' => 'warning',
            'processing' => 'info',
            'completed' => 'success',
            'failed' => 'danger',
            'deleted' => 'gray',
            default => 'gray',
        };
    }

    public static function getStatusIcon(string $status): string
    {
        return match ($status) {
            'pending' => 'heroicon-o-clock',
            'processing' => 'heroicon-o-arrow-path',
            'completed' => 'heroicon-o-check-circle',
            'failed' => 'heroicon-o-x-circle',
            'deleted' => 'heroicon-o-trash',
            default => 'heroicon-o-question-mark-circle',
        };
    }
    
    public function getCurrentStatusColor(): string
    {
        return $this::getStatusColor($this->getState());
    }
    
    public function getCurrentStatusIcon(): string
    {
        return $this::getStatusIcon($this->getState());
    }
    
    public function getCurrentTimeRemaining(): ?int
    {
        $record = $this->getRecord();
        return $this::calculateTimeRemaining($record);
    }
}
