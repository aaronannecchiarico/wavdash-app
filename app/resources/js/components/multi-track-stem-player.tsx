import { SoundcloudWaveform } from '@/components/soundcloud-waveform';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
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

export function MultiTrackStemPlayer({ stems, uploadId, analysis }: MultiTrackStemPlayerProps) {
    const [globalPlaying, setGlobalPlaying] = useState(false);
    const [players, setPlayers] = useState<Record<string, StemPlayerState>>({});
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const syncRef = useRef<boolean>(false);
    const progressUpdateRef = useRef<NodeJS.Timeout | null>(null);

    // Initialize player states
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
                // For R2 storage, use public_path if available (converted OGG), otherwise fallback to file_path
                const r2BaseUrl = import.meta.env.VITE_R2_URL || '';
                const stemPath = stem.public_path || stem.file_path;
                return `${r2BaseUrl}/${stemPath}`;
            }
            // For local storage, use the download route
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
        updatePlayerState(stemType, {
            wavesurfer: ws,
            isLoading: false,
        });

        // Set initial volume
        const playerState = players[stemType];
        if (playerState) {
            ws.setVolume(playerState.isMuted ? 0 : playerState.volume / 100);
        }

        // Set duration from first loaded track
        if (duration === 0) {
            setDuration(ws.getDuration());
        }

        // Listen for time updates
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
            // Pause all
            Object.values(players).forEach((player) => {
                if (player.wavesurfer && !player.isLoading) {
                    player.wavesurfer.pause();
                }
            });
            setGlobalPlaying(false);
            if (progressUpdateRef.current) {
                clearInterval(progressUpdateRef.current);
                progressUpdateRef.current = null;
            }
        } else {
            // Play all
            Object.values(players).forEach((player) => {
                if (player.wavesurfer && !player.isLoading) {
                    player.wavesurfer.play();
                }
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

        // Seek all tracks to the new position
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
        if (syncRef.current) return; // Ignore if this is part of global sync

        syncRef.current = true;

        // Update the global current time
        setCurrentTime(seekTime);

        // Seek all other tracks to the same position
        Object.entries(players).forEach(([type, player]) => {
            if (type !== stemType && player.wavesurfer && !player.isLoading) {
                const progress = seekTime / duration;
                player.wavesurfer.seekTo(progress);
            }
        });

        syncRef.current = false;
    };

    const allLoaded = stems.every((stem) => !players[stem.stem_type]?.isLoading);

    // Brutalist color assignments for stems
    const stemColors = ['bg-[var(--neo-green)]', 'bg-[var(--neo-pink)]', 'bg-[var(--neo-yellow)]', 'bg-[var(--neo-blue)]'];

    return (
        <div className="neo-border neo-shadow bg-[var(--neo-bg-primary)] dark:bg-[var(--neo-black)]">
            <div className="neo-border-b bg-[var(--neo-black)] p-4">
                <h2 className="text-xl font-black tracking-wider text-[var(--neo-white)] uppercase">STEM TRACKS</h2>
            </div>
            <div className="space-y-4 p-6">
                {/* Global Controls */}
                <div className="neo-border-b flex items-center gap-4 pb-4">
                    <Button
                        onClick={handleGlobalPlayPause}
                        variant="default"
                        size="lg"
                        className="neo-shadow hover:neo-shadow-hover h-12 w-12 bg-[var(--neo-green)] hover:translate-x-1 hover:translate-y-1 hover:bg-[var(--neo-pink)]"
                        disabled={!allLoaded}
                    >
                        {!allLoaded ? (
                            <Loader2 className="h-6 w-6 animate-spin text-[var(--neo-black)]" />
                        ) : globalPlaying ? (
                            <PauseIcon className="h-6 w-6 text-[var(--neo-black)]" />
                        ) : (
                            <PlayIcon className="h-6 w-6 text-[var(--neo-black)]" />
                        )}
                    </Button>

                    {/* Global Progress Slider */}
                    <div className="flex flex-1 items-center gap-3">
                        <Button variant="default" size="sm" className="min-w-[50px] font-mono text-[var(--neo-black)]">
                            {formatTime(currentTime)}
                        </Button>
                        <div className="neo-border neo-shadow-hover flex-1 bg-[var(--neo-blue)]/20 p-2">
                            <Slider
                                value={[currentTime]}
                                onValueChange={handleProgressChange}
                                onValueCommit={handleProgressCommit}
                                max={duration || 100}
                                step={0.1}
                                className="neo-slider w-full"
                                disabled={!allLoaded || duration === 0}
                            />
                        </div>
                        <Button variant="secondary" size="sm" className="min-w-[50px] font-mono text-[var(--neo-white)]">
                            {formatTime(duration)}
                        </Button>
                    </div>

                    {/* Track Info */}
                    {analysis && (
                        <div className="flex items-center gap-2 text-xs font-black tracking-wider uppercase">
                            {analysis.musical_key && (
                                <>
                                    <span className="text-[var(--neo-text-primary)]">KEY</span>
                                    <div className="neo-border bg-[var(--neo-green)] px-2 py-1 text-[var(--neo-black)]">{analysis.musical_key}</div>
                                </>
                            )}
                            {analysis.bpm && (
                                <>
                                    <span className="text-[var(--neo-text-primary)]">BPM</span>
                                    <div className="neo-border bg-[var(--neo-pink)] px-2 py-1 text-[var(--neo-white)]">{analysis.bpm}</div>
                                </>
                            )}
                        </div>
                    )}
                </div>

                {/* Stem Tracks */}
                <div className="space-y-4">
                    {stems.map((stem, index) => {
                        const player = players[stem.stem_type] || {
                            wavesurfer: null,
                            isLoading: true,
                            volume: 80,
                            isMuted: false,
                        };

                        const stemColor = stemColors[index % stemColors.length];

                        return (
                            <div key={stem.id} className={`neo-border neo-shadow p-4 ${stemColor}`}>
                                <div className="mb-3 flex items-center justify-between">
                                    <h4 className="font-black tracking-wider text-[var(--neo-black)] uppercase">
                                        {stem.stem_type.replace('_', ' ')}
                                    </h4>
                                    <div className="flex space-x-2">
                                        <Button
                                            variant="secondary"
                                            size="sm"
                                            className="neo-border border-[var(--neo-black)] font-black text-[var(--neo-black)] uppercase hover:bg-[var(--neo-black)] hover:text-[var(--neo-white)]"
                                            disabled={player.isLoading}
                                        >
                                            SOLO
                                        </Button>
                                        <Button
                                            onClick={() => handleMuteToggle(stem.stem_type)}
                                            variant="secondary"
                                            size="sm"
                                            className="neo-border border-[var(--neo-black)] font-black text-[var(--neo-black)] uppercase hover:bg-[var(--neo-black)] hover:text-[var(--neo-white)]"
                                            disabled={player.isLoading}
                                        >
                                            {player.isMuted ? 'UNMUTE' : 'MUTE'}
                                        </Button>
                                    </div>
                                </div>

                                {/* Individual waveform */}
                                <div className="neo-border mb-3 bg-[var(--neo-black)]/10 p-2">
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
                                <div className="flex items-center space-x-4">
                                    <span className="font-mono text-sm font-bold text-[var(--neo-black)]">VOL</span>
                                    <div className="neo-border neo-shadow-hover flex-1 bg-[var(--neo-white)] p-1">
                                        <Slider
                                            value={[player.volume]}
                                            onValueChange={(value) => handleVolumeChange(stem.stem_type, value)}
                                            max={100}
                                            step={1}
                                            className="neo-slider w-full"
                                            disabled={player.isLoading}
                                        />
                                    </div>
                                    <span className="w-10 text-right font-mono text-sm font-bold text-[var(--neo-black)]">{player.volume}%</span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
