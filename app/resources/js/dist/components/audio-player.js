import WaveSurfer from 'wavesurfer.js';

export default function audioPlayer({ audioUrl, duration = null }) {
    return {
        wavesurfer: null,
        isPlaying: false,
        isLoading: true,
        currentTime: '00:00',
        totalDuration: '00:00',
        progress: 0,
        error: null,

        init() {
            console.log('Audio player initializing with URL:', audioUrl);

            // Set totalDuration from duration parameter if provided
            if (duration) {
                this.totalDuration = this.formatTime(duration);
            }

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
                    if (!duration) {
                        this.totalDuration = this.formatTime(this.wavesurfer.getDuration());
                    }
                });

                this.wavesurfer.on('play', () => {
                    console.log('WaveSurfer playing');
                    this.isPlaying = true;
                });

                this.wavesurfer.on('pause', () => {
                    console.log('WaveSurfer paused');
                    this.isPlaying = false;
                });

                this.wavesurfer.on('audioprocess', () => {
                    this.updateProgress();
                });

                this.wavesurfer.on('seek', () => {
                    this.updateProgress();
                });

                this.wavesurfer.on('error', (error) => {
                    console.error('WaveSurfer error:', error);
                    this.error = 'Error loading audio file';
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
            if (!this.wavesurfer) {
                console.error('WaveSurfer not initialized');
                return;
            }

            try {
                if (this.isPlaying) {
                    this.wavesurfer.pause();
                } else {
                    this.wavesurfer.play();
                }
            } catch (error) {
                console.error('Error toggling playback:', error);
                this.error = 'Playback error: ' + error.message;
            }
        },

        updateProgress() {
            if (!this.wavesurfer) return;

            try {
                const current = this.wavesurfer.getCurrentTime();
                const total = this.wavesurfer.getDuration();

                this.currentTime = this.formatTime(current);
                this.progress = total ? (current / total) * 100 : 0;
            } catch (error) {
                console.error('Error updating progress:', error);
            }
        },

        formatTime(seconds) {
            if (!seconds || !isFinite(seconds)) return '00:00';

            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.floor(seconds % 60);

            return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        },

        destroy() {
            console.log('Destroying WaveSurfer instance');
            if (this.wavesurfer) {
                this.wavesurfer.destroy();
                this.wavesurfer = null;
            }
        },
    };
}
