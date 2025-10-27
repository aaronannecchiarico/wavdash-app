<x-dynamic-component
    :component="$getEntryWrapperView()"
    :entry="$entry"
>
    <div {{ $getExtraAttributeBag() }} class="filament-infolists-audio-player-entry">
        @if($getRecord()?->getStreamPath())
            <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <!-- Waveform Container -->
                <div id="waveform-{{ $getRecord()->id }}" class="w-full bg-gray-50 rounded dark:bg-gray-700 mb-4" style="min-height: 60px;"></div>

                <!-- Controls -->
                <div class="flex justify-center">
                    <!-- Play Button -->
                    <button
                        id="play-btn-{{ $getRecord()->id }}"
                        class="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onclick="togglePlayPause{{ $getRecord()->id }}()"
                    >
                        <svg class="h-5 w-5 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>

                <!-- Pure JavaScript Implementation -->
                <script>
                    (function() {
                        let wavesurfer{{ $getRecord()->id }} = null;
                        let isPlaying{{ $getRecord()->id }} = false;

                        // Wait for WaveSurfer to load
                        function initWaveSurfer{{ $getRecord()->id }}() {
                            if (typeof WaveSurfer === 'undefined') {
                                setTimeout(initWaveSurfer{{ $getRecord()->id }}, 100);
                                return;
                            }

                            try {
                                const container = document.getElementById('waveform-{{ $getRecord()->id }}');
                                if (!container) return;

                                wavesurfer{{ $getRecord()->id }} = WaveSurfer.create({
                                    container: container,
                                    waveColor: '#3b82f6',
                                    progressColor: '#1d4ed8',
                                    normalize: true,
                                    height: 60,
                                    responsive: true,
                                    mediaControls: true,
                                });

                                wavesurfer{{ $getRecord()->id }}.load(@js($getRecord()->getStreamPath()));

                                wavesurfer{{ $getRecord()->id }}.on('play', function() {
                                    isPlaying{{ $getRecord()->id }} = true;
                                    updateButton{{ $getRecord()->id }}();
                                });

                                wavesurfer{{ $getRecord()->id }}.on('pause', function() {
                                    isPlaying{{ $getRecord()->id }} = false;
                                    updateButton{{ $getRecord()->id }}();
                                });

                                wavesurfer{{ $getRecord()->id }}.on('ready', function() {
                                    console.log('WaveSurfer ready for upload {{ $getRecord()->id }}');
                                });

                            } catch (error) {
                                console.error('WaveSurfer init error:', error);
                            }
                        }

                        function updateButton{{ $getRecord()->id }}() {
                            const btn = document.getElementById('play-btn-{{ $getRecord()->id }}');
                            if (!btn) return;

                            if (isPlaying{{ $getRecord()->id }}) {
                                btn.innerHTML = '<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>';
                            } else {
                                btn.innerHTML = '<svg class="h-5 w-5 ml-0.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" /></svg>';
                            }
                        }

                        window.togglePlayPause{{ $getRecord()->id }} = function() {
                            if (!wavesurfer{{ $getRecord()->id }}) {
                                console.log('WaveSurfer not ready');
                                return;
                            }

                            wavesurfer{{ $getRecord()->id }}.playPause();
                        };

                        // Initialize when page loads
                        if (document.readyState === 'loading') {
                            document.addEventListener('DOMContentLoaded', initWaveSurfer{{ $getRecord()->id }});
                        } else {
                            initWaveSurfer{{ $getRecord()->id }}();
                        }
                    })();
                </script>
            </div>
        @else
            <div class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center dark:border-gray-700 dark:bg-gray-800">
                <x-heroicon-o-musical-note class="mx-auto h-8 w-8 text-gray-400 dark:text-gray-500" />
                <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">No audio file available</p>
            </div>
        @endif
    </div>
</x-dynamic-component>
