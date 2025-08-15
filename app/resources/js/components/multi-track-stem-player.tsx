import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { SoundcloudWaveform } from '@/components/soundcloud-waveform';
import { Loader2, PauseIcon, PlayIcon, Volume2, VolumeX } from 'lucide-react';
import { useState, useRef, useCallback, useEffect } from 'react';
import type WaveSurfer from 'wavesurfer.js';
import type { UploadAnalysis } from '@/types';

interface Stem {
    id: number;
    stem_type: string;
    stem_type_name?: string;
    file_path: string;
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
        stems.forEach(stem => {
            initialPlayers[stem.stem_type] = {
                wavesurfer: null,
                isLoading: true,
                volume: 80,
                isMuted: false,
            };
        });
        setPlayers(initialPlayers);
    }, [stems]);

    const getStemUrl = useCallback((stem: Stem) => {
        if (stem.storage_type === 'r2') {
            // For R2 storage, construct the full URL
            const r2BaseUrl = import.meta.env.VITE_R2_URL || '';
            return `${r2BaseUrl}/${stem.file_path}`;
        }
        // For local storage, use the download route
        return route('uploads.stems.download', { 
            upload: uploadId, 
            stemType: stem.stem_type 
        });
    }, [uploadId]);

    const getStemIcon = (stemType: string) => {
        switch (stemType) {
            case 'vocals': return '🎤';
            case 'drums': return '🥁';
            case 'bass': return '🎸';
            case 'other': return '🎹';
            default: return '🎵';
        }
    };

    const updatePlayerState = (stemType: string, updates: Partial<StemPlayerState>) => {
        setPlayers(prev => ({
            ...prev,
            [stemType]: { ...prev[stemType], ...updates }
        }));
    };

    const handleWavesurferReady = (stemType: string, ws: WaveSurfer) => {
        updatePlayerState(stemType, { 
            wavesurfer: ws, 
            isLoading: false 
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
            Object.values(players).forEach(player => {
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
            Object.values(players).forEach(player => {
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
        Object.values(players).forEach(player => {
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

    const allLoaded = stems.every(stem => !players[stem.stem_type]?.isLoading);

    return (
        <Card className="bg-slate-50 dark:bg-gray-900 border-slate-200 dark:border-gray-700">
            <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                    🎵 Stem Player
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Global Controls */}
                <div className="flex items-center gap-4 pb-4 border-b border-slate-200 dark:border-gray-700">
                    <Button
                        onClick={handleGlobalPlayPause}
                        variant="outline"
                        size="icon"
                        className="h-10 w-10 rounded-full bg-slate-900 hover:bg-slate-800 dark:bg-gray-800 dark:hover:bg-gray-700 border-slate-300 dark:border-gray-600 text-white"
                        disabled={!allLoaded}
                    >
                        {!allLoaded ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        ) : globalPlaying ? (
                            <PauseIcon className="h-5 w-5" />
                        ) : (
                            <PlayIcon className="h-5 w-5" />
                        )}
                    </Button>
                    
                    {/* Global Progress Slider */}
                    <div className="flex items-center gap-3 flex-1">
                        <span className="text-xs text-slate-600 dark:text-gray-400 min-w-[40px]">
                            {formatTime(currentTime)}
                        </span>
                        <div className="flex-1">
                            <Slider
                                value={[currentTime]}
                                onValueChange={handleProgressChange}
                                onValueCommit={handleProgressCommit}
                                max={duration || 100}
                                step={0.1}
                                className="w-full"
                                disabled={!allLoaded || duration === 0}
                            />
                        </div>
                        <span className="text-xs text-slate-600 dark:text-gray-400 min-w-[40px] text-right">
                            {formatTime(duration)}
                        </span>
                    </div>
                    
                    {/* Track Info */}
                    {analysis && (
                        <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-gray-400">
                            {analysis.musical_key && (
                                <>
                                    <span>KEY</span>
                                    <span className="bg-slate-200 dark:bg-gray-700 px-2 py-1 rounded text-slate-900 dark:text-white">{analysis.musical_key}</span>
                                </>
                            )}
                            {analysis.bpm && (
                                <>
                                    <span>BPM</span>
                                    <span className="bg-slate-200 dark:bg-gray-700 px-2 py-1 rounded text-slate-900 dark:text-white">{analysis.bpm}</span>
                                </>
                            )}
                        </div>
                    )}
                </div>
                
                {/* Stem Tracks */}
                <div className="space-y-2">
                    {stems.map((stem) => {
                        const player = players[stem.stem_type] || { 
                            wavesurfer: null, 
                            isLoading: true, 
                            volume: 80, 
                            isMuted: false 
                        };
                        
                        const getStemColor = (stemType: string) => {
                            switch (stemType) {
                                case 'vocals': return 'bg-blue-500/20 dark:bg-blue-500/20';
                                case 'drums': return 'bg-red-500/20 dark:bg-red-500/20';
                                case 'bass': return 'bg-yellow-500/20 dark:bg-yellow-500/20';
                                case 'other': return 'bg-green-500/20 dark:bg-green-500/20';
                                default: return 'bg-purple-500/20 dark:bg-purple-500/20';
                            }
                        };
                        
                        return (
                            <div key={stem.id} className="flex items-center gap-3 py-2">
                                {/* Track Label */}
                                <div className="flex items-center gap-2 w-20">
                                    <span className="text-sm">{getStemIcon(stem.stem_type)}</span>
                                    <span className="text-sm font-medium text-slate-700 dark:text-gray-300 capitalize">
                                        {stem.stem_type}
                                    </span>
                                </div>
                                
                                {/* Volume Controls */}
                                <div className="flex items-center gap-2 w-24">
                                    <Button
                                        onClick={() => handleMuteToggle(stem.stem_type)}
                                        variant="ghost"
                                        size="icon"
                                        className="h-6 w-6 hover:bg-slate-200 dark:hover:bg-gray-700 text-slate-700 dark:text-gray-300"
                                        disabled={player.isLoading}
                                    >
                                        {player.isMuted ? (
                                            <VolumeX className="h-3 w-3" />
                                        ) : (
                                            <Volume2 className="h-3 w-3" />
                                        )}
                                    </Button>
                                    <span className="text-xs text-slate-600 dark:text-gray-400 w-8 text-center">
                                        {player.volume}
                                    </span>
                                </div>
                                
                                {/* Compact Waveform */}
                                <div className="flex-1 h-12 relative">
                                    <div className={`absolute inset-0 ${getStemColor(stem.stem_type)} rounded`}></div>
                                    <div className="absolute inset-0 overflow-hidden rounded" style={{ height: '48px' }}>
                                        <SoundcloudWaveform
                                            url={getStemUrl(stem)}
                                            onReady={(ws) => handleWavesurferReady(stem.stem_type, ws)}
                                            onPlay={() => handleStemPlay(stem.stem_type)}
                                            onPause={() => handleStemPause(stem.stem_type)}
                                            onFinish={() => setGlobalPlaying(false)}
                                            onSeek={(time) => handleStemSeek(stem.stem_type, time)}
                                            height={48}
                                            compact={true}
                                        />
                                    </div>
                                </div>
                                
                                {/* Volume Slider */}
                                <div className="w-16">
                                    <Slider
                                        value={[player.volume]}
                                        onValueChange={(value) => handleVolumeChange(stem.stem_type, value)}
                                        max={100}
                                        step={1}
                                        className="w-full"
                                        disabled={player.isLoading}
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>
            </CardContent>
        </Card>
    );
}