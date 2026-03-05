import { SoundcloudWaveform } from '@/components/soundcloud-waveform';
import { Button } from '@/components/ui/button';
import { Loader2, PauseIcon, PlayIcon, Volume2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import type WaveSurfer from 'wavesurfer.js';

interface AudioPlayerProps {
    url: string;
    title?: string;
    className?: string;
}

export function AudioPlayer({ url, title, className = '' }: AudioPlayerProps) {
    const [wavesurfer, setWavesurfer] = useState<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(0.5);

    const handlePlayPause = () => {
        if (wavesurfer) {
            wavesurfer.playPause();
        }
    };

    const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVolume = parseFloat(e.target.value);
        setVolume(newVolume);
        if (wavesurfer) {
            wavesurfer.setVolume(newVolume);
        }
    };

    // Update time display
    useEffect(() => {
        if (wavesurfer) {
            const updateTime = () => {
                setCurrentTime(wavesurfer.getCurrentTime());
            };

            wavesurfer.on('timeupdate', updateTime);
            return () => {
                wavesurfer.un('timeupdate', updateTime);
            };
        }
    }, [wavesurfer]);

    // Set initial volume when wavesurfer is ready
    useEffect(() => {
        if (wavesurfer) {
            wavesurfer.setVolume(volume);
        }
    }, [wavesurfer, volume]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className={`audio-player neo-border neo-shadow bg-[var(--neo-bg-primary)] p-6 dark:bg-[var(--neo-black)] ${className}`}>
            {title && <h3 className="neo-border-b mb-4 pb-2 text-lg font-black tracking-widest text-[var(--neo-text-primary)] uppercase">{title}</h3>}

            <div className="flex items-center space-x-6">
                {/* Brutalist play button */}
                <Button
                    onClick={handlePlayPause}
                    variant="default"
                    size="lg"
                    className="neo-shadow hover:neo-shadow-hover h-16 w-16 bg-[var(--neo-green)] hover:translate-x-1 hover:translate-y-1 hover:bg-[var(--neo-pink)]"
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <Loader2 className="h-8 w-8 animate-spin text-[var(--neo-black)]" />
                    ) : isPlaying ? (
                        <PauseIcon className="h-8 w-8 text-[var(--neo-black)]" />
                    ) : (
                        <PlayIcon className="h-8 w-8 text-[var(--neo-black)]" />
                    )}
                </Button>

                {/* Waveform with brutalist styling */}
                <div className="neo-border neo-shadow-hover flex-1 bg-[var(--neo-yellow)]/20 p-4">
                    <SoundcloudWaveform
                        url={url}
                        onReady={(ws) => {
                            setWavesurfer(ws);
                            setDuration(ws.getDuration());
                            setIsLoading(false);
                        }}
                        onPlay={() => setIsPlaying(true)}
                        onPause={() => setIsPlaying(false)}
                        onFinish={() => setIsPlaying(false)}
                    />
                </div>
            </div>

            {/* Control bar with brutalist buttons */}
            <div className="mt-4 flex items-center justify-between">
                <div className="flex space-x-2">
                    <Button variant="default" size="sm" className="font-mono text-[var(--neo-black)]">
                        {formatTime(currentTime)}
                    </Button>
                    <Button variant="secondary" size="sm" className="font-mono text-[var(--neo-white)]">
                        {formatTime(duration)}
                    </Button>
                </div>

                <div className="flex items-center space-x-3">
                    <Volume2 className="h-4 w-4 text-[var(--neo-text-primary)]" />
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={volume}
                        onChange={handleVolumeChange}
                        className="neo-border slider-thumb:w-4 slider-thumb:h-4 slider-thumb:bg-[var(--neo-green)] slider-thumb:border-2 slider-thumb:border-[var(--neo-black)] slider-thumb:cursor-pointer hover:slider-thumb:bg-[var(--neo-pink)] h-2 w-20 bg-[var(--neo-bg-secondary)]"
                        style={{
                            background: `linear-gradient(to right, var(--neo-green) 0%, var(--neo-green) ${volume * 100}%, var(--neo-bg-secondary) ${volume * 100}%, var(--neo-bg-secondary) 100%)`,
                        }}
                    />
                </div>
            </div>
        </div>
    );
}
