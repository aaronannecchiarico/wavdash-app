import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useWavesurfer } from '@wavesurfer/react';
import type WaveSurfer from 'wavesurfer.js';
import { formatDuration } from '@/lib/formatters';

interface SoundcloudWaveformProps {
    url: string;
    onReady?: (wavesurfer: WaveSurfer) => void;
    onPlay?: () => void;
    onPause?: () => void;
    onFinish?: () => void;
}

export function SoundcloudWaveform({
    url,
    onReady,
    onPlay,
    onPause,
    onFinish,
}: SoundcloudWaveformProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const hoverRef = useRef<HTMLDivElement>(null);
    const [duration, setDuration] = useState<number>(0);
    const [isDarkMode, setIsDarkMode] = useState(false);

    useEffect(() => {
        const checkDarkMode = () => document.documentElement.classList.contains('dark');
        setIsDarkMode(checkDarkMode());

        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.attributeName === 'class') {
                    setIsDarkMode(checkDarkMode());
                }
            }
        });

        observer.observe(document.documentElement, { attributes: true });

        return () => observer.disconnect();
    }, []);

    const { waveColor, progressColor } = useMemo(() => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) return { waveColor: '', progressColor: '' };

        canvas.height = 100;

        // Light mode gradients
        const lightModeWaveGradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
        lightModeWaveGradient.addColorStop(0, '#94a3b8'); // slate-400
        lightModeWaveGradient.addColorStop((canvas.height * 0.7) / canvas.height, '#94a3b8');
        lightModeWaveGradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#f8fafc'); // White line (slate-50)
        lightModeWaveGradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#f8fafc');
        lightModeWaveGradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#cbd5e1'); // slate-300
        lightModeWaveGradient.addColorStop(1, '#cbd5e1');

        const lightModeProgressGradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
        lightModeProgressGradient.addColorStop(0, '#6366f1'); // indigo-500
        lightModeProgressGradient.addColorStop((canvas.height * 0.7) / canvas.height, '#4f46e5'); // indigo-600
        lightModeProgressGradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#f8fafc'); // White line (slate-50)
        lightModeProgressGradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#f8fafc');
        lightModeProgressGradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#818cf8'); // indigo-400
        lightModeProgressGradient.addColorStop(1, '#a5b4fc'); // indigo-300

        // Dark mode gradients
        const darkModeWaveGradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
        darkModeWaveGradient.addColorStop(0, '#475569'); // slate-600
        darkModeWaveGradient.addColorStop((canvas.height * 0.7) / canvas.height, '#475569');
        darkModeWaveGradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#0f172a'); // slate-900
        darkModeWaveGradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#0f172a');
        darkModeWaveGradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#334155'); // slate-700
        darkModeWaveGradient.addColorStop(1, '#334155');

        const darkModeProgressGradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
        darkModeProgressGradient.addColorStop(0, '#818cf8'); // indigo-400
        darkModeProgressGradient.addColorStop((canvas.height * 0.7) / canvas.height, '#6366f1'); // indigo-500
        darkModeProgressGradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#1e1b4b'); // indigo-950
        darkModeProgressGradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#1e1b4b');
        darkModeProgressGradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#4f46e5'); // indigo-600
        darkModeProgressGradient.addColorStop(1, '#4338ca'); // indigo-700

        return {
            waveColor: isDarkMode ? darkModeWaveGradient : lightModeWaveGradient,
            progressColor: isDarkMode ? darkModeProgressGradient : lightModeProgressGradient,
        };
    }, [isDarkMode]);

    const { wavesurfer, isPlaying, currentTime } = useWavesurfer({
        container: containerRef,
        waveColor: waveColor,
        progressColor: progressColor,
        barWidth: 2,
        barGap: 1,
        barRadius: 1,
        url: url,
        height: 75,
    });

    useEffect(() => {
        if (wavesurfer) {
            wavesurfer.setOptions({
                waveColor: waveColor,
                progressColor: progressColor,
            });
        }
    }, [waveColor, progressColor, wavesurfer]);

    useEffect(() => {
        if (!wavesurfer) return;

        const subscriptions = [
            wavesurfer.on('ready', () => {
                setDuration(wavesurfer.getDuration());
                if (onReady) onReady(wavesurfer);
            }),
            wavesurfer.on('play', () => {
                if (onPlay) onPlay();
            }),
            wavesurfer.on('pause', () => {
                if (onPause) onPause();
            }),
            wavesurfer.on('finish', () => {
                if (onFinish) onFinish();
            }),
        ];

        return () => {
            subscriptions.forEach((unsub) => unsub());
        };
    }, [wavesurfer, onReady, onPlay, onPause, onFinish]);

    // Handle hover effect
    useEffect(() => {
        const container = containerRef.current;
        const hover = hoverRef.current;

        if (!container || !hover) return;

        const handlePointerMove = (e: PointerEvent) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            hover.style.width = `${x}px`;
        };

        container.addEventListener('pointermove', handlePointerMove);

        return () => {
            container.removeEventListener('pointermove', handlePointerMove);
        };
    }, []);

    // Handle play/pause on interaction
    const handleInteraction = useCallback(() => {
        if (wavesurfer) {
            wavesurfer.playPause();
        }
    }, [wavesurfer]);

    return (
        <div className="relative w-full soundcloud-waveform group">
            <div
                ref={containerRef}
                onClick={handleInteraction}
                className="cursor-pointer relative"
            >
                <div
                    ref={hoverRef}
                    className="absolute left-0 top-0 z-10 pointer-events-none h-full w-0 mix-blend-overlay bg-white/50 dark:bg-white/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100"
                />
            </div>

            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                <span>{formatDuration(isFinite(currentTime) ? currentTime : 0)}</span>
                <span>{formatDuration(isFinite(duration) ? duration : 0)}</span>
            </div>
        </div>
    );
}
