<x-dynamic-component
    :component="$getEntryWrapperView()"
    :entry="$entry"
>
    <div {{ $getExtraAttributeBag() }} class="filament-infolists-audio-player-entry">
        @if($getRecord()?->getStreamPath())
            <div class="space-y-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <!-- Audio Title -->
                @if($getRecord()?->title ?? $getRecord()?->filename)
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {{ $getRecord()->title ?? $getRecord()->filename }}
                    </h4>
                @endif

                <!-- HTML5 Audio Player -->
                <div class="w-full">
                    <audio 
                        controls 
                        preload="metadata"
                        class="w-full h-10"
                        style="border-radius: 6px;"
                    >
                        <source src="{{ $getRecord()->getStreamPath() }}" type="audio/ogg">
                        <p class="text-sm text-red-600 dark:text-red-400">
                            Your browser does not support the audio element.
                        </p>
                    </audio>
                </div>

                <!-- Optional: Duration info -->
                @if($getRecord()?->duration_seconds)
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                        Duration: {{ gmdate('H:i:s', $getRecord()->duration_seconds) }}
                    </div>
                @endif
            </div>
        @else
            <div class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center dark:border-gray-700 dark:bg-gray-800">
                <x-heroicon-o-musical-note class="mx-auto h-4 w-4 text-gray-400 dark:text-gray-500" />
                <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">No audio file available</p>
            </div>
        @endif
    </div>
</x-dynamic-component>
