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
        <div className={`studio-card p-5 ${className}`}>
            {title && (
                <h3 className="font-sans font-semibold text-sm text-foreground mb-4 pb-3 border-b border-[--border]">
                    {title}
                </h3>
            )}

            <div className="flex items-center gap-4">
                {/* Play button */}
                <Button
                    onClick={handlePlayPause}
                    variant="default"
                    size="icon"
                    className="h-10 w-10 shrink-0 rounded-full shadow-amber"
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : isPlaying ? (
                        <PauseIcon className="h-4 w-4" />
                    ) : (
                        <PlayIcon className="h-4 w-4" />
                    )}
                </Button>

                {/* Waveform */}
                <div className="flex-1 rounded-[--radius-md] bg-[--surface-2] px-3 py-2">
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

            {/* Control bar */}
            <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-2 font-mono text-xs text-muted-foreground">
                    <span>{formatTime(currentTime)}</span>
                    <span>/</span>
                    <span>{formatTime(duration)}</span>
                </div>

                <div className="flex items-center gap-2">
                    <Volume2 className="h-3.5 w-3.5 text-muted-foreground" />
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={volume}
                        onChange={handleVolumeChange}
                        className="h-1.5 w-20 cursor-pointer accent-[--amber]"
                        style={{
                            background: `linear-gradient(to right, var(--amber) 0%, var(--amber) ${volume * 100}%, var(--surface-3) ${volume * 100}%, var(--surface-3) 100%)`,
                        }}
                    />
                </div>
            </div>
        </div>
    );
}
