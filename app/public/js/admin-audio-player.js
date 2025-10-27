// Alpine.js Audio Player Component for Filament Admin
document.addEventListener('alpine:init', () => {
    Alpine.data('audioPlayer', ({ audioUrl, title = null, duration = null }) => ({
        wavesurfer: null,
        isPlaying: false,
        isLoading: true,
        error: null,

        init() {
            console.log('Audio player initializing with URL:', audioUrl);
            
            // Check if WaveSurfer is available
            if (typeof WaveSurfer === 'undefined') {
                console.error('WaveSurfer library not loaded');
                this.error = 'WaveSurfer library not loaded';
                this.isLoading = false;
                return;
            }
            
            // Add a timeout to ensure we don't stay loading forever
            setTimeout(() => {
                if (this.isLoading) {
                    console.warn('Audio player timed out during loading');
                    this.isLoading = false;
                    if (!this.error) {
                        this.error = 'Audio loading timed out';
                    }
                }
            }, 10000); // 10 second timeout
            
            // Initialize on next tick to ensure DOM is ready
            this.$nextTick(() => {
                this.initWaveSurfer();
            });
        },

        initWaveSurfer() {
            try {
                console.log('Creating WaveSurfer instance...');
                
                // Check if container exists
                if (!this.$refs.waveform) {
                    throw new Error('Waveform container not found');
                }

                // Create WaveSurfer instance
                this.wavesurfer = WaveSurfer.create({
                    container: this.$refs.waveform,
                    waveColor: '#e5e7eb',
                    progressColor: '#3b82f6',
                    cursorColor: '#1f2937',
                    barWidth: 2,
                    barRadius: 1,
                    responsive: true,
                    height: 60,
                    normalize: true,
                    backend: 'WebAudio',
                    mediaControls: false,
                });

                console.log('WaveSurfer instance created, loading audio...');

                // Load the audio file
                this.wavesurfer.load(audioUrl);

                // Set up event listeners
                this.wavesurfer.on('ready', () => {
                    console.log('WaveSurfer ready');
                    this.isLoading = false;
                    this.error = null;
                });

                this.wavesurfer.on('play', () => {
                    console.log('WaveSurfer playing');
                    this.isPlaying = true;
                });

                this.wavesurfer.on('pause', () => {
                    console.log('WaveSurfer paused');
                    this.isPlaying = false;
                });

                this.wavesurfer.on('error', (error) => {
                    console.error('WaveSurfer error:', error);
                    this.error = 'Error loading audio file: ' + (error.message || error);
                    this.isLoading = false;
                });

                this.wavesurfer.on('load', () => {
                    console.log('WaveSurfer load event');
                });

                this.wavesurfer.on('loading', (percent) => {
                    console.log('WaveSurfer loading:', percent + '%');
                });

            } catch (error) {
                console.error('Failed to initialize WaveSurfer:', error);
                this.error = 'Failed to initialize audio player: ' + error.message;
                this.isLoading = false;
            }
        },

        togglePlayPause() {
            console.log('Toggle play/pause clicked, wavesurfer:', !!this.wavesurfer);
            
            if (!this.wavesurfer) {
                console.error('WaveSurfer not initialized');
                this.error = 'Audio player not ready';
                return;
            }

            try {
                if (this.isPlaying) {
                    console.log('Pausing...');
                    this.wavesurfer.pause();
                } else {
                    console.log('Playing...');
                    this.wavesurfer.play();
                }
            } catch (error) {
                console.error('Error toggling playback:', error);
                this.error = 'Playback error: ' + error.message;
            }
        },

        destroy() {
            console.log('Destroying WaveSurfer instance');
            if (this.wavesurfer) {
                this.wavesurfer.destroy();
                this.wavesurfer = null;
            }
        }
    }));
});