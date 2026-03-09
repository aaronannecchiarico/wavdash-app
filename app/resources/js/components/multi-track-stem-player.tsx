import { SoundcloudWaveform } from '@/components/soundcloud-waveform';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';
import type { UploadAnalysis } from '@/types';
import { Loader2, PauseIcon, PlayIcon } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import type WaveSurfer from 'wavesurfer.js';

interface Stem {
    id: number;
    stem_type: string;
    stem_type_name?: string;
    file_path: string;
    public_path?: string;
    storage_type: string;
}

interface StemPlayerState {
    wavesurfer: WaveSurfer | null;
    isLoading: boolean;
    volume: number;
    isMuted: boolean;
}

interface MultiTrackStemPlayerProps {
    stems: Stem[];
    uploadId: number;
    analysis?: UploadAnalysis;
}

// Per-stem accent colors (header bg + waveform tint)
const stemAccent: Record<string, { header: string; bar: string }> = {
    vocals: { header: 'bg-[--amber]/10 border-[--amber]/20', bar: 'var(--amber)' },
    drums:  { header: 'bg-[--jade]/10 border-[--jade]/20',   bar: 'var(--jade)' },
    bass:   { header: 'bg-blue-500/10 border-blue-300/20',    bar: '#60a5fa' },
    guitar: { header: 'bg-violet-500/10 border-violet-300/20', bar: '#a78bfa' },
    piano:  { header: 'bg-rose-500/10 border-rose-300/20',     bar: '#fb7185' },
    other:  { header: 'bg-[--surface-2] border-[--border]',   bar: 'var(--muted-foreground)' },
};

const STEM_ORDER = ['vocals', 'drums', 'bass', 'guitar', 'piano', 'other'];

const getAccent = (stemType: string) => stemAccent[stemType] || stemAccent.other;

export function MultiTrackStemPlayer({ stems, uploadId, analysis }: MultiTrackStemPlayerProps) {
    const [globalPlaying, setGlobalPlaying] = useState(false);
    const [players, setPlayers] = useState<Record<string, StemPlayerState>>({});
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const syncRef = useRef<boolean>(false);
    const progressUpdateRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        const initialPlayers: Record<string, StemPlayerState> = {};
        stems.forEach((stem) => {
            initialPlayers[stem.stem_type] = {
                wavesurfer: null,
                isLoading: true,
                volume: 80,
                isMuted: false,
            };
        });
        setPlayers(initialPlayers);
    }, [stems]);

    const getStemUrl = useCallback(
        (stem: Stem) => {
            if (stem.storage_type === 'r2') {
                const r2BaseUrl = import.meta.env.VITE_R2_URL || '';
                const stemPath = stem.public_path || stem.file_path;
                return `${r2BaseUrl}/${stemPath}`;
            }
            return route('uploads.stems.download', {
                upload: uploadId,
                stemType: stem.stem_type,
            });
        },
        [uploadId],
    );

    const updatePlayerState = (stemType: string, updates: Partial<StemPlayerState>) => {
        setPlayers((prev) => ({
            ...prev,
            [stemType]: { ...prev[stemType], ...updates },
        }));
    };

    const handleWavesurferReady = (stemType: string, ws: WaveSurfer) => {
        updatePlayerState(stemType, { wavesurfer: ws, isLoading: false });
        const playerState = players[stemType];
        if (playerState) {
            ws.setVolume(playerState.isMuted ? 0 : playerState.volume / 100);
        }
        if (duration === 0) {
            setDuration(ws.getDuration());
        }
        ws.on('timeupdate', (time) => {
            if (!isDragging) {
                setCurrentTime(time);
            }
        });
        ws.on('finish', () => {
            setGlobalPlaying(false);
            setCurrentTime(0);
        });
    };

    const handleGlobalPlayPause = () => {
        syncRef.current = true;
        if (globalPlaying) {
            Object.values(players).forEach((player) => {
                if (player.wavesurfer && !player.isLoading) player.wavesurfer.pause();
            });
            setGlobalPlaying(false);
            if (progressUpdateRef.current) {
                clearInterval(progressUpdateRef.current);
                progressUpdateRef.current = null;
            }
        } else {
            Object.values(players).forEach((player) => {
                if (player.wavesurfer && !player.isLoading) player.wavesurfer.play();
            });
            setGlobalPlaying(true);
        }
        syncRef.current = false;
    };

    const handleVolumeChange = (stemType: string, volume: number[]) => {
        const newVolume = volume[0];
        const player = players[stemType];
        updatePlayerState(stemType, { volume: newVolume });
        if (player?.wavesurfer && !player.isLoading) {
            player.wavesurfer.setVolume(player.isMuted ? 0 : newVolume / 100);
        }
    };

    const handleMuteToggle = (stemType: string) => {
        const player = players[stemType];
        if (!player) return;
        const newMuted = !player.isMuted;
        updatePlayerState(stemType, { isMuted: newMuted });
        if (player.wavesurfer && !player.isLoading) {
            player.wavesurfer.setVolume(newMuted ? 0 : player.volume / 100);
        }
    };

    const handleProgressChange = (value: number[]) => {
        const newTime = value[0];
        setCurrentTime(newTime);
        setIsDragging(true);
        Object.values(players).forEach((player) => {
            if (player.wavesurfer && !player.isLoading) {
                player.wavesurfer.seekTo(newTime / duration);
            }
        });
    };

    const handleProgressCommit = () => {
        setIsDragging(false);
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleStemPlay = (stemType: string) => {
        if (syncRef.current) return;
        setGlobalPlaying(true);
        Object.entries(players).forEach(([type, player]) => {
            if (type !== stemType && player.wavesurfer && !player.isLoading) {
                player.wavesurfer.play();
            }
        });
    };

    const handleStemPause = (stemType: string) => {
        if (syncRef.current) return;
        setGlobalPlaying(false);
        Object.entries(players).forEach(([type, player]) => {
            if (type !== stemType && player.wavesurfer && !player.isLoading) {
                player.wavesurfer.pause();
            }
        });
    };

    const handleStemSeek = (stemType: string, seekTime: number) => {
        if (syncRef.current) return;
        syncRef.current = true;
        setCurrentTime(seekTime);
        Object.entries(players).forEach(([type, player]) => {
            if (type !== stemType && player.wavesurfer && !player.isLoading) {
                player.wavesurfer.seekTo(seekTime / duration);
            }
        });
        syncRef.current = false;
    };

    const allLoaded = stems.every((stem) => !players[stem.stem_type]?.isLoading);

    return (
        <div className="studio-card overflow-hidden">
            {/* Player header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-[--border] bg-[--surface-2]">
                <h2 className="font-sans font-semibold text-sm text-foreground">Stem tracks</h2>
                {analysis && (
                    <div className="flex items-center gap-2">
                        {analysis.musical_key && (
                            <Badge variant="default" className="font-mono text-xs">{analysis.musical_key}</Badge>
                        )}
                        {analysis.bpm && (
                            <Badge variant="secondary" className="font-mono text-xs">{analysis.bpm} BPM</Badge>
                        )}
                    </div>
                )}
            </div>

            <div className="p-5 space-y-5">
                {/* Global controls */}
                <div className="flex items-center gap-4 pb-4 border-b border-[--border]">
                    <Button
                        onClick={handleGlobalPlayPause}
                        variant="default"
                        size="icon"
                        className="h-10 w-10 rounded-full shrink-0 shadow-amber"
                        disabled={!allLoaded}
                    >
                        {!allLoaded ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : globalPlaying ? (
                            <PauseIcon className="h-4 w-4" />
                        ) : (
                            <PlayIcon className="h-4 w-4" />
                        )}
                    </Button>

                    <div className="flex flex-1 items-center gap-3">
                        <span className="font-mono text-xs text-muted-foreground w-10 shrink-0">{formatTime(currentTime)}</span>
                        <div className="flex-1">
                            <Slider
                                value={[currentTime]}
                                onValueChange={handleProgressChange}
                                onValueCommit={handleProgressCommit}
                                max={duration || 100}
                                step={0.1}
                                className="w-full [&_[data-slot=slider-thumb]]:bg-[--amber] [&_[data-slot=slider-range]]:bg-[--amber]"
                                disabled={!allLoaded || duration === 0}
                            />
                        </div>
                        <span className="font-mono text-xs text-muted-foreground w-10 text-right shrink-0">{formatTime(duration)}</span>
                    </div>
                </div>

                {/* Stem tracks */}
                <div className="space-y-3">
                    {[...stems].sort((a, b) => {
                        const aIdx = STEM_ORDER.indexOf(a.stem_type);
                        const bIdx = STEM_ORDER.indexOf(b.stem_type);
                        return (aIdx === -1 ? 99 : aIdx) - (bIdx === -1 ? 99 : bIdx);
                    }).map((stem) => {
                        const player = players[stem.stem_type] || {
                            wavesurfer: null,
                            isLoading: true,
                            volume: 80,
                            isMuted: false,
                        };
                        const accent = getAccent(stem.stem_type);

                        return (
                            <div key={stem.id} className={cn('rounded-[--radius-md] border p-4', accent.header)}>
                                {/* Stem header */}
                                <div className="flex items-center justify-between mb-3">
                                    <h4 className="font-sans font-medium text-sm text-foreground capitalize">
                                        {stem.stem_type_name || stem.stem_type}
                                    </h4>
                                    <div className="flex gap-1.5">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-7 px-2 text-xs"
                                            disabled={player.isLoading}
                                        >
                                            Solo
                                        </Button>
                                        <Button
                                            onClick={() => handleMuteToggle(stem.stem_type)}
                                            variant={player.isMuted ? 'default' : 'ghost'}
                                            size="sm"
                                            className="h-7 px-2 text-xs"
                                            disabled={player.isLoading}
                                        >
                                            {player.isMuted ? 'Unmute' : 'Mute'}
                                        </Button>
                                    </div>
                                </div>

                                {/* Waveform */}
                                <div className="rounded-[--radius-sm] bg-background/50 px-2 py-1.5 mb-3">
                                    <SoundcloudWaveform
                                        url={getStemUrl(stem)}
                                        onReady={(ws) => handleWavesurferReady(stem.stem_type, ws)}
                                        onPlay={() => handleStemPlay(stem.stem_type)}
                                        onPause={() => handleStemPause(stem.stem_type)}
                                        onFinish={() => setGlobalPlaying(false)}
                                        onSeek={(time) => handleStemSeek(stem.stem_type, time)}
                                        height={60}
                                        compact={false}
                                    />
                                </div>

                                {/* Volume control */}
                                <div className="flex items-center gap-3">
                                    <span className="font-mono text-xs text-muted-foreground w-6 shrink-0">Vol</span>
                                    <Slider
                                        value={[player.volume]}
                                        onValueChange={(value) => handleVolumeChange(stem.stem_type, value)}
                                        max={100}
                                        step={1}
                                        className="flex-1 [&_[data-slot=slider-thumb]]:bg-[--amber] [&_[data-slot=slider-range]]:bg-[--amber]"
                                        disabled={player.isLoading}
                                    />
                                    <span className="font-mono text-xs text-muted-foreground w-8 text-right shrink-0">
                                        {player.volume}%
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
