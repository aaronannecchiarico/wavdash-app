import { Button } from '@/components/ui/button';
import { SoundcloudWaveform } from '@/components/soundcloud-waveform';
import { Loader2, PauseIcon, PlayIcon, SkipBack, SkipForward, Volume2 } from 'lucide-react';
import { useState, useEffect } from 'react';
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

    const handlePlayPause = () => {
        if (wavesurfer) {
            wavesurfer.playPause();
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

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className={`audio-player neo-border neo-shadow bg-[var(--neo-bg-primary)] dark:bg-[var(--neo-black)] p-6 ${className}`}>
            {title && (
                <h3 className="mb-4 text-lg font-black uppercase tracking-widest text-[var(--neo-text-primary)] neo-border-b pb-2">
                    {title}
                </h3>
            )}
            
            <div className="flex items-center space-x-6">
                {/* Brutalist play button */}
                <Button
                    onClick={handlePlayPause}
                    variant="default"
                    size="lg"
                    className="w-16 h-16 bg-[var(--neo-green)] hover:bg-[var(--neo-pink)] neo-shadow hover:neo-shadow-hover hover:translate-x-1 hover:translate-y-1"
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
                <div className="flex-1 neo-border neo-shadow-hover bg-[var(--neo-yellow)]/20 p-4">
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
            <div className="mt-4 flex justify-between items-center">
                <div className="flex space-x-2">
                    <Button variant="accent" size="sm" className="font-mono text-[var(--neo-black)]">
                        {formatTime(currentTime)}
                    </Button>
                    <Button variant="secondary" size="sm" className="font-mono text-[var(--neo-white)]">
                        {formatTime(duration)}
                    </Button>
                </div>
                
                <div className="flex space-x-2">
                    <Button variant="outline" size="icon" className="neo-shadow hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5">
                        <SkipBack className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="icon" className="neo-shadow hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5">
                        <SkipForward className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="icon" className="neo-shadow hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5">
                        <Volume2 className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}