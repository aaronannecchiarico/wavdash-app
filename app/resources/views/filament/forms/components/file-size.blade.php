@php
    use App\Filament\Infolists\Components\FileSizeEntry;
    $record = $getRecord();
    $bytes = $record?->size ?? $record?->file_size ?? 0;
    $formatted = FileSizeEntry::formatBytes($bytes);
@endphp

<div class="filament-forms-file-size-component">
    @if($bytes !== null && $bytes > 0)
        <div class="inline-flex items-center space-x-2 rounded-lg bg-gray-100 px-3 py-2 text-sm dark:bg-gray-700">
            <!-- File Size Icon -->
            <x-heroicon-o-document class="h-4 w-4 text-gray-500 dark:text-gray-400" />
            
            <!-- Formatted Size -->
            <span class="font-medium text-gray-900 dark:text-gray-100">
                {{ $formatted }}
            </span>
            
            <!-- Raw Bytes (tooltip on hover) -->
            <span 
                class="text-xs text-gray-500 dark:text-gray-400 cursor-help"
                title="{{ number_format($bytes) }} bytes"
            >
                ({{ number_format($bytes) }} bytes)
            </span>
        </div>
        
        <!-- Visual Size Bar (optional) -->
        @if($bytes > 1024) {{-- Only show for files larger than 1KB --}}
            <div class="mt-2">
                <div class="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>Size:</span>
                    <div class="flex-1 h-1.5 bg-gray-200 rounded-full dark:bg-gray-600 max-w-32">
                        <div 
                            class="h-1.5 rounded-full {{ $bytes > 50 * 1024 * 1024 ? 'bg-red-500' : ($bytes > 10 * 1024 * 1024 ? 'bg-yellow-500' : 'bg-green-500') }}"
                            style="width: {{ min(($bytes / (100 * 1024 * 1024)) * 100, 100) }}%"
                        ></div>
                    </div>
                </div>
            </div>
        @endif
    @else
        <div class="inline-flex items-center space-x-2 rounded-lg bg-gray-50 px-3 py-2 text-sm dark:bg-gray-800">
            <x-heroicon-o-question-mark-circle class="h-4 w-4 text-gray-400 dark:text-gray-500" />
            <span class="text-gray-500 dark:text-gray-400">Unknown size</span>
        </div>
    @endif
</div>