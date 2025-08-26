<div class="filament-forms-audio-player-component">
    @if($getRecord()?->stream_url)
        <div class="space-y-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <!-- Audio Title -->
            @if($getRecord()?->title ?? $getRecord()?->filename)
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {{ $getRecord()->title ?? $getRecord()->filename }}
                </h4>
            @endif

            <!-- Audio Player Controls -->
            <div class="flex items-center space-x-3" x-data="audioPlayer(@js($getRecord()->stream_url))" x-init="init()">
                <!-- Play/Pause Button -->
                <button 
                    type="button"
                    @click="togglePlayPause()"
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-primary-600 text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
                    :disabled="!audioLoaded"
                >
                    <x-heroicon-o-play class="h-5 w-5" x-show="!isPlaying" />
                    <x-heroicon-o-pause class="h-5 w-5" x-show="isPlaying" />
                </button>

                <!-- Progress Bar -->
                <div class="flex-1">
                    <div class="relative">
                        <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-600">
                            <div 
                                class="h-2 rounded-full bg-primary-600 transition-all duration-150"
                                :style="`width: ${progress}%`"
                            ></div>
                        </div>
                        <input 
                            type="range" 
                            class="absolute inset-0 h-2 w-full cursor-pointer opacity-0"
                            min="0" 
                            max="100" 
                            step="0.1"
                            x-model.number="progress"
                            @input="seekTo($event.target.value)"
                        />
                    </div>
                </div>

                <!-- Time Display -->
                <div class="text-xs text-gray-500 dark:text-gray-400 font-mono min-w-[80px] text-right">
                    <span x-text="formatTime(currentTime)">0:00</span>
                    <span>/</span>
                    <span x-text="formatTime(duration)">{{ $getRecord()?->duration_seconds ? gmdate('i:s', $getRecord()->duration_seconds) : '0:00' }}</span>
                </div>

                <!-- Volume Control -->
                <div class="flex items-center space-x-2">
                    <button 
                        type="button"
                        @click="toggleMute()"
                        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                        <x-heroicon-o-speaker-wave class="h-4 w-4" x-show="!isMuted && volume > 0" />
                        <x-heroicon-o-speaker-x-mark class="h-4 w-4" x-show="isMuted || volume === 0" />
                    </button>
                    <input 
                        type="range" 
                        class="w-16 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-600"
                        min="0" 
                        max="100" 
                        x-model.number="volume"
                        @input="setVolume($event.target.value)"
                    />
                </div>
            </div>

            <!-- Waveform Visualization Placeholder -->
            <div class="h-16 rounded bg-gray-100 dark:bg-gray-700">
                <!-- Future waveform visualization -->
                <div class="flex h-full items-center justify-center text-xs text-gray-500">
                    Waveform visualization coming soon
                </div>
            </div>

            <!-- Loading State -->
            <div x-show="!audioLoaded" class="text-xs text-gray-500 dark:text-gray-400">
                Loading audio...
            </div>

            <!-- Error State -->
            <div x-show="hasError" class="text-xs text-red-600 dark:text-red-400">
                <x-heroicon-o-exclamation-triangle class="inline h-4 w-4" />
                Failed to load audio file
            </div>
        </div>

        <script>
        function audioPlayer(audioUrl) {
            return {
                audio: null,
                audioUrl: audioUrl,
                audioLoaded: false,
                isPlaying: false,
                isMuted: false,
                hasError: false,
                currentTime: 0,
                duration: 0,
                progress: 0,
                volume: 80,
                
                init() {
                    this.audio = new Audio(this.audioUrl);
                    
                    this.audio.addEventListener('loadedmetadata', () => {
                        this.duration = this.audio.duration;
                        this.audioLoaded = true;
                    });
                    
                    this.audio.addEventListener('timeupdate', () => {
                        this.currentTime = this.audio.currentTime;
                        this.progress = (this.currentTime / this.duration) * 100;
                    });
                    
                    this.audio.addEventListener('ended', () => {
                        this.isPlaying = false;
                        this.progress = 0;
                        this.currentTime = 0;
                    });
                    
                    this.audio.addEventListener('error', () => {
                        this.hasError = true;
                    });
                    
                    this.audio.volume = this.volume / 100;
                },
                
                togglePlayPause() {
                    if (this.isPlaying) {
                        this.audio.pause();
                    } else {
                        this.audio.play();
                    }
                    this.isPlaying = !this.isPlaying;
                },
                
                seekTo(percentage) {
                    const time = (percentage / 100) * this.duration;
                    this.audio.currentTime = time;
                },
                
                toggleMute() {
                    this.audio.muted = !this.audio.muted;
                    this.isMuted = this.audio.muted;
                },
                
                setVolume(volume) {
                    this.audio.volume = volume / 100;
                    this.isMuted = volume === 0;
                },
                
                formatTime(seconds) {
                    if (isNaN(seconds)) return '0:00';
                    const minutes = Math.floor(seconds / 60);
                    const secs = Math.floor(seconds % 60);
                    return `${minutes}:${secs.toString().padStart(2, '0')}`;
                }
            };
        }
        </script>
    @else
        <div class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center dark:border-gray-700 dark:bg-gray-800">
            <x-heroicon-o-musical-note class="mx-auto h-8 w-8 text-gray-400 dark:text-gray-500" />
            <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">No audio file available</p>
        </div>
    @endif
</div>