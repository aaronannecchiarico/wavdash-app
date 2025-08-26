@php
    use App\Filament\Infolists\Components\ProcessingStatusEntry;
    
    $record = $getRecord();
    $status = $record?->status ?? 'unknown';
    $progress = $record?->progress ?? 0;
    $errorMessage = $record?->error_message;
    $submittedAt = $record?->submitted_at;
    $completedAt = $record?->completed_at;
    $estimatedTimeRemaining = ProcessingStatusEntry::calculateTimeRemaining($record);
    
    $statusColor = ProcessingStatusEntry::getStatusColor($status);
    $statusIcon = ProcessingStatusEntry::getStatusIcon($status);
@endphp

<div class="filament-forms-processing-status-component">
    <div class="space-y-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <!-- Status Header -->
        <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <!-- Status Badge -->
                <div class="inline-flex items-center space-x-1.5 rounded-full px-2.5 py-1 text-xs font-medium 
                    @if($statusColor === 'success') bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300
                    @elseif($statusColor === 'danger') bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300
                    @elseif($statusColor === 'warning') bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300
                    @elseif($statusColor === 'info') bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300
                    @else bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300
                    @endif">
                    <x-dynamic-component :component="$statusIcon" class="h-3 w-3" />
                    <span class="capitalize">{{ $status }}</span>
                </div>
                
                <!-- Processing Animation -->
                @if($status === 'processing')
                    <div class="flex space-x-1">
                        <div class="h-1.5 w-1.5 bg-blue-600 rounded-full animate-pulse"></div>
                        <div class="h-1.5 w-1.5 bg-blue-600 rounded-full animate-pulse animation-delay-75"></div>
                        <div class="h-1.5 w-1.5 bg-blue-600 rounded-full animate-pulse animation-delay-150"></div>
                    </div>
                @endif
            </div>
            
            <!-- Progress Percentage -->
            @if($status === 'processing' && $progress !== null && $progress > 0)
                <span class="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {{ $progress }}%
                </span>
            @endif
        </div>

        <!-- Progress Bar -->
        @if($status === 'processing' && $progress !== null)
            <div class="w-full">
                <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-600">
                    <div 
                        class="h-2 rounded-full bg-blue-600 transition-all duration-300 ease-out"
                        style="width: {{ $progress }}%"
                    ></div>
                </div>
            </div>
        @endif

        <!-- Time Information -->
        <div class="grid grid-cols-1 gap-2 text-xs text-gray-500 dark:text-gray-400 sm:grid-cols-2">
            @if($submittedAt)
                <div class="flex items-center space-x-1">
                    <x-heroicon-o-clock class="h-3 w-3" />
                    <span>Started: {{ $submittedAt->format('M j, Y H:i') }}</span>
                </div>
            @endif
            
            @if($completedAt)
                <div class="flex items-center space-x-1">
                    <x-heroicon-o-check-circle class="h-3 w-3" />
                    <span>Completed: {{ $completedAt->format('M j, Y H:i') }}</span>
                </div>
            @endif
            
            @if($estimatedTimeRemaining && $status === 'processing')
                <div class="flex items-center space-x-1">
                    <x-heroicon-o-clock class="h-3 w-3" />
                    <span>
                        ETA: {{ $estimatedTimeRemaining > 60 ? 
                            floor($estimatedTimeRemaining / 60) . 'm ' . ($estimatedTimeRemaining % 60) . 's' : 
                            $estimatedTimeRemaining . 's' 
                        }}
                    </span>
                </div>
            @endif
        </div>

        <!-- Error Message -->
        @if($errorMessage && $status === 'failed')
            <div class="rounded-md bg-red-50 p-3 dark:bg-red-900/50">
                <div class="flex items-start space-x-2">
                    <x-heroicon-o-exclamation-triangle class="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                    <div class="text-sm text-red-800 dark:text-red-300">
                        <p class="font-medium">Error Details:</p>
                        <p class="mt-1">{{ $errorMessage }}</p>
                    </div>
                </div>
            </div>
        @endif

        <!-- Status-specific Messages -->
        @if($status === 'pending')
            <div class="rounded-md bg-yellow-50 p-3 dark:bg-yellow-900/50">
                <div class="flex items-center space-x-2">
                    <x-heroicon-o-clock class="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                    <span class="text-sm text-yellow-800 dark:text-yellow-300">
                        Task is queued and waiting to be processed
                    </span>
                </div>
            </div>
        @elseif($status === 'completed')
            <div class="rounded-md bg-green-50 p-3 dark:bg-green-900/50">
                <div class="flex items-center space-x-2">
                    <x-heroicon-o-check-circle class="h-4 w-4 text-green-600 dark:text-green-400" />
                    <span class="text-sm text-green-800 dark:text-green-300">
                        Task completed successfully
                        @if($submittedAt && $completedAt)
                            in {{ $submittedAt->diffForHumans($completedAt, true) }}
                        @endif
                    </span>
                </div>
            </div>
        @elseif($status === 'deleted')
            <div class="rounded-md bg-gray-50 p-3 dark:bg-gray-900/50">
                <div class="flex items-center space-x-2">
                    <x-heroicon-o-trash class="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    <span class="text-sm text-gray-800 dark:text-gray-300">
                        Task has been deleted
                    </span>
                </div>
            </div>
        @endif
    </div>
</div>

<style>
    .animation-delay-75 {
        animation-delay: 0.075s;
    }
    .animation-delay-150 {
        animation-delay: 0.15s;
    }
</style>