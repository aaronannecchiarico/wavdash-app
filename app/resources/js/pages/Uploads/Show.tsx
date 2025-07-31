import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import { formatDistance } from 'date-fns';
import { PencilIcon, Trash2Icon as TrashIcon, PlayIcon, PauseIcon } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface Upload {
    id: number;
    title: string;
    description: string | null;
    filename: string;
    mime_type: string;
    size: number;
    status: string;
    stream_url: string | null;
    created_at: string;
    updated_at: string;
    user: {
        id: number;
        name: string;
    };
}

interface Props {
    upload: Upload;
}

export default function Show({ upload }: Props) {
    const uploadData = 'data' in upload && upload.data ? (upload.data as Upload) : upload;
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const visualizerContainerRef = useRef<HTMLDivElement | null>(null);
    const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
    const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);
    const [currentTime, setCurrentTime] = useState<number>(0);
    const [duration, setDuration] = useState<number>(0);
    const [containerWidth, setContainerWidth] = useState<number>(600);

    // Initialize Audio Context and load audio file
    useEffect(() => {
        if (uploadData.status === 'ready' && uploadData.stream_url) {
            // Create audio context
            const context = new (window.AudioContext || (window as any).webkitAudioContext)();
            setAudioContext(context);

            const fetchAudio = async () => {
                try {
                    const response = await fetch(uploadData.stream_url!);
                    const arrayBuffer = await response.arrayBuffer();

                    // Decode audio data
                    context.decodeAudioData(arrayBuffer).then(buffer => {
                        setAudioBuffer(buffer);

                        // Set duration from the audio buffer (more reliable than audioRef.duration)
                        // Double-check the duration is valid
                        if (buffer && isFinite(buffer.duration) && buffer.duration > 0) {
                            console.log('Setting duration from buffer:', buffer.duration);
                            setDuration(buffer.duration);
                        } else {
                            console.warn('Invalid buffer duration:', buffer?.duration);
                            // Try to get it from audio element as fallback
                            if (audioRef.current && isFinite(audioRef.current.duration) && audioRef.current.duration > 0) {
                                console.log('Using audio element duration instead:', audioRef.current.duration);
                                setDuration(audioRef.current.duration);
                            } else {
                                console.warn('Both buffer and audio element durations are invalid');
                            }
                        }

                        // Draw waveform once audio is loaded
                        drawWaveform(buffer);
                    }).catch(err => {
                        console.error('Error decoding audio data:', err);
                    });
                } catch (error) {
                    console.error('Error fetching audio file:', error);
                }
            };

            fetchAudio();

            // Clean up audio context on unmount
            return () => {
                if (context.state !== 'closed') {
                    context.close();
                }
            };
        }
    }, [uploadData.status, uploadData.stream_url]);

    // Update container width when component mounts or window resizes
    useEffect(() => {
        const updateContainerWidth = () => {
            if (visualizerContainerRef.current) {
                const width = visualizerContainerRef.current.getBoundingClientRect().width;
                setContainerWidth(width);

                // Redraw waveform when container size changes
                if (audioBuffer) {
                    drawWaveform(audioBuffer);
                }
            }
        };

        // Initial width calculation
        updateContainerWidth();

        // Update on window resize
        window.addEventListener('resize', updateContainerWidth);

        return () => {
            window.removeEventListener('resize', updateContainerWidth);
        };
    }, [audioBuffer]);

    // Function to draw audio waveform on canvas
    const drawWaveform = (buffer: AudioBuffer) => {
        if (!canvasRef.current) return;

        const canvas = canvasRef.current;
        const canvasCtx = canvas.getContext('2d');
        if (!canvasCtx) return;

        // Set canvas dimensions
        canvas.width = containerWidth;
        canvas.height = 75;

        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        canvasCtx.clearRect(0, 0, width, height);

        // Set waveform style
        canvasCtx.fillStyle = '#6366F1'; // Indigo color

        // Get audio data
        const audioData = buffer.getChannelData(0);
        const step = Math.ceil(audioData.length / width);
        const amp = height / 2;

        // Draw waveform
        for (let i = 0; i < width; i++) {
            let min = 1.0;
            let max = -1.0;

            // Find min and max values in this segment
            for (let j = 0; j < step; j++) {
                const datum = audioData[i * step + j];
                if (datum < min) min = datum;
                if (datum > max) max = datum;
            }

            // Draw bar for this segment (from min to max)
            const barWidth = 2;
            const barHeight = (max - min) * amp;
            const posX = i * (barWidth + 1);
            const posY = (1 + min) * amp;

            canvasCtx.fillRect(posX, posY, barWidth, barHeight);
        }
    };

    // Toggle play/pause
    const togglePlayPause = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    // Handle audio ended event
    const handleAudioEnded = () => {
        setIsPlaying(false);
    };

    // Update progress overlay during playback
    useEffect(() => {
        let animationFrame: number | null = null;

        const updatePlaybackPosition = () => {
            try {
                // Safety check for required objects
                if (!audioRef.current || !canvasRef.current || !audioBuffer) {
                    return;
                }

                // Get current playback time (with validation)
                const currentTime = audioRef.current.currentTime;
                if (isFinite(currentTime)) {
                    setCurrentTime(currentTime);
                }

                // Validate duration one more time if needed
                let localDuration = duration;
                if (!isFinite(localDuration) || localDuration <= 0) {
                    // Try getting it from audio element
                    if (audioRef.current && isFinite(audioRef.current.duration) && audioRef.current.duration > 0) {
                        localDuration = audioRef.current.duration;
                        setDuration(localDuration);
                    } else if (audioBuffer && isFinite(audioBuffer.duration) && audioBuffer.duration > 0) {
                        localDuration = audioBuffer.duration;
                        setDuration(localDuration);
                    } else {
                        // Default to a reasonable value to avoid division by zero
                        localDuration = 1;
                    }
                }

                // Draw progress overlay
                const canvas = canvasRef.current;
                const ctx = canvas.getContext('2d');

                if (ctx) {
                    const width = canvas.width;
                    const height = canvas.height;

                    // Calculate progress safely
                    const progress = isFinite(currentTime) && isFinite(localDuration) && localDuration > 0
                        ? Math.max(0, Math.min(1, currentTime / localDuration))
                        : 0;

                    // Redraw waveform
                    drawWaveform(audioBuffer);

                    // Draw playback position indicator
                    const progressX = width * progress;
                    ctx.fillStyle = 'rgba(99, 102, 241, 0.3)'; // Indigo with opacity
                    ctx.fillRect(0, 0, progressX, height);

                    // Draw position line
                    ctx.fillStyle = '#4F46E5';
                    ctx.fillRect(progressX - 1, 0, 2, height);
                }

                if (isPlaying) {
                    animationFrame = requestAnimationFrame(updatePlaybackPosition);
                }
            } catch (error) {
                console.error('Error updating playback position:', error);
            }
        };

        if (isPlaying && audioRef.current) {
            animationFrame = requestAnimationFrame(updatePlaybackPosition);
        }

        return () => {
            if (animationFrame !== null) {
                cancelAnimationFrame(animationFrame);
            }
        };
    }, [isPlaying, audioBuffer, duration, containerWidth]);

    // Format time in MM:SS format
    const formatTime = (timeInSeconds: number): string => {
        if (isNaN(timeInSeconds)) return "00:00";

        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);

        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    // Handle audio metadata loaded
    const handleMetadataLoaded = () => {
        console.log('Audio metadata loaded');

        // Try to get duration from audio element
        if (audioRef.current && isFinite(audioRef.current.duration) && audioRef.current.duration > 0) {
            console.log('Setting duration from audio element metadata:', audioRef.current.duration);
            setDuration(audioRef.current.duration);
            return;
        }

        // Fallback to audioBuffer duration
        if (audioBuffer && isFinite(audioBuffer.duration) && audioBuffer.duration > 0) {
            console.log('Setting duration from audio buffer:', audioBuffer.duration);
            setDuration(audioBuffer.duration);
            return;
        }

        console.warn('Could not determine audio duration from metadata');
    };

    // Handle seeking when user clicks on the progress bar
    const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
        try {
            // Only proceed if we have a valid audio element and duration
            if (!audioRef.current || !duration || duration <= 0 || !isFinite(duration)) {
                console.log('Skipping seek: Invalid audio reference or duration');
                return;
            }

            const progressBar = e.currentTarget;
            const rect = progressBar.getBoundingClientRect();

            // Calculate the click position
            const offsetX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
            const clickPositionRatio = offsetX / rect.width;

            // Calculate new time with strict bounds checking
            let newTime = clickPositionRatio * duration;

            // Extra safety checks
            if (!isFinite(newTime) || newTime < 0) {
                console.log('Invalid seek time (setting to 0):', newTime);
                newTime = 0;
            } else if (newTime > duration) {
                console.log('Seek time beyond duration (clamping):', newTime, duration);
                newTime = duration * 0.99; // Slightly before the end to avoid edge cases
            }

            // Apply the new time
            audioRef.current.currentTime = newTime;
            setCurrentTime(newTime);

            // Force redraw of waveform with new position
            if (audioBuffer && canvasRef.current) {
                const canvas = canvasRef.current;
                const ctx = canvas.getContext('2d');

                if (ctx) {
                    drawWaveform(audioBuffer);

                    // Update progress indicator
                    const width = canvas.width;
                    const height = canvas.height;
                    const progressX = width * clickPositionRatio;

                    ctx.fillStyle = 'rgba(99, 102, 241, 0.3)';
                    ctx.fillRect(0, 0, progressX, height);

                    ctx.fillStyle = '#4F46E5';
                    ctx.fillRect(progressX - 1, 0, 2, height);
                }
            }
        } catch (error) {
            console.error('Error during seek operation:', error);
        }
    };

    // Format file size to human-readable format
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // Get status badge color based on status
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'ready':
                return 'bg-green-100 text-green-800';
            case 'processing':
                return 'bg-blue-100 text-blue-800';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const breadcrumbs: BreadcrumbItem[] = [
        { title: 'Music Library', href: route('uploads.index') },
        { title: uploadData.title, href: route('uploads.show', uploadData.id), description: 'View track details' },
    ];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={uploadData.title} />

            <div className="mx-auto max-w-4xl py-8">
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>{uploadData.title}</CardTitle>
                                <CardDescription>
                                    Uploaded {formatDistance(new Date(uploadData.created_at), new Date(), { addSuffix: true })}
                                </CardDescription>
                            </div>
                            <span className={`inline-block rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(uploadData.status)}`}>
                                {uploadData.status.charAt(0).toUpperCase() + uploadData.status.slice(1)}
                            </span>
                        </div>
                    </CardHeader>

                    <CardContent className="space-y-6">
                        {uploadData.description && (
                            <div>
                                <h3 className="mb-2 text-sm font-medium text-gray-700">Description</h3>
                                <p className="text-gray-600">{uploadData.description}</p>
                            </div>
                        )}

                        <div>
                            <h3 className="mb-2 text-sm font-medium text-gray-700">File Details</h3>
                            <dl className="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Filename</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{uploadData.filename}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Type</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{uploadData.mime_type}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Size</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{formatFileSize(uploadData.size)}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                                    <dd className="mt-1 text-sm text-gray-900">
                                        {formatDistance(new Date(uploadData.updated_at), new Date(), { addSuffix: true })}
                                    </dd>
                                </div>
                            </dl>
                        </div>

                        {uploadData.status === 'ready' && uploadData.stream_url && (
                            <div>
                                <h3 className="mb-2 text-sm font-medium text-gray-700">Preview</h3>

                                <div className="mb-4">
                                    <audio
                                        ref={audioRef}
                                        src={uploadData.stream_url}
                                        className="hidden"
                                        onEnded={handleAudioEnded}
                                        onLoadedMetadata={handleMetadataLoaded}
                                        onDurationChange={(e) => {
                                            const newDuration = e.currentTarget.duration;
                                            if (isFinite(newDuration) && newDuration > 0) {
                                                console.log('Duration changed:', newDuration);
                                                setDuration(newDuration);
                                            }
                                        }}
                                        onTimeUpdate={(e) => {
                                            const newTime = e.currentTarget.currentTime;
                                            if (isFinite(newTime)) {
                                                setCurrentTime(newTime);
                                            }
                                        }}
                                    />

                                    <div className="flex items-center space-x-4">
                                        <Button
                                            onClick={togglePlayPause}
                                            variant="outline"
                                            size="icon"
                                            className="rounded-full h-10 w-10"
                                            disabled={!audioBuffer}
                                        >
                                            {!audioBuffer ? (
                                                <svg className="animate-spin h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                            ) : isPlaying ? <PauseIcon className="h-5 w-5" /> : <PlayIcon className="h-5 w-5" />}
                                        </Button>

                                        <div className="w-full">
                                            <div
                                                className="bg-gray-100 rounded-lg overflow-hidden"
                                                ref={visualizerContainerRef}
                                            >
                                                <canvas
                                                    ref={canvasRef}
                                                    className="w-full h-[75px]"
                                                ></canvas>
                                            </div>

                                            {/* Progress Bar */}
                                            <div
                                                className="h-2 bg-gray-200 rounded-full mt-2 cursor-pointer relative"
                                                onClick={handleSeek}
                                            >
                                                <div
                                                    className="h-full bg-indigo-600 rounded-full"
                                                    style={{
                                                        width: `${isFinite(currentTime) && isFinite(duration) && duration > 0
                                                            ? Math.min(100, (currentTime / duration) * 100)
                                                            : 0}%`
                                                    }}
                                                ></div>
                                            </div>

                                            <div className="flex justify-between mt-2 text-xs text-gray-500">
                                                <span>{formatTime(isFinite(currentTime) ? currentTime : 0)}</span>
                                                <span>{formatTime(isFinite(duration) ? duration : 0)}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="flex justify-between bg-gray-50">
                        <Link href={route('uploads.edit', uploadData.id)}>
                            <Button variant="outline">
                                <PencilIcon className="mr-2 h-4 w-4" />
                                Edit
                            </Button>
                        </Link>

                        <Link
                            href={route('uploads.destroy', uploadData.id)}
                            method="delete"
                            as="button"
                            type="button"
                            className="inline-flex items-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-xs font-semibold tracking-widest text-white uppercase hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none"
                        >
                            <TrashIcon className="mr-2 h-4 w-4" />
                            Delete
                        </Link>
                    </CardFooter>
                </Card>
            </div>
        </AppLayout>
    );
}
