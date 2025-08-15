import { Button } from '@/components/ui/button';
import { SoundcloudWaveform } from '@/components/soundcloud-waveform';
import { Loader2, PauseIcon, PlayIcon } from 'lucide-react';
import { useState } from 'react';
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

    const handlePlayPause = () => {
        if (wavesurfer) {
            wavesurfer.playPause();
        }
    };

    return (
        <div className={`audio-player ${className}`}>
            {title && (
                <h3 className="mb-2 text-sm font-medium text-foreground/80 dark:text-foreground/90">
                    {title}
                </h3>
            )}
            
            <div className="flex items-center space-x-4">
                <Button
                    onClick={handlePlayPause}
                    variant="outline"
                    size="icon"
                    className="h-10 w-10 rounded-full"
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                    ) : isPlaying ? (
                        <PauseIcon className="h-5 w-5" />
                    ) : (
                        <PlayIcon className="h-5 w-5" />
                    )}
                </Button>

                <div className="w-full">
                    <SoundcloudWaveform
                        url={url}
                        onReady={(ws) => {
                            setWavesurfer(ws);
                            setIsLoading(false);
                        }}
                        onPlay={() => setIsPlaying(true)}
                        onPause={() => setIsPlaying(false)}
                        onFinish={() => setIsPlaying(false)}
                    />
                </div>
            </div>
        </div>
    );
}