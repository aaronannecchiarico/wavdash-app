import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import WavesurferPlayer from '@wavesurfer/react';
import type WaveSurfer from 'wavesurfer.js';
import { formatDistance } from 'date-fns';
import { PauseIcon, PencilIcon, PlayIcon, Trash2Icon as TrashIcon } from 'lucide-react';
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
    const visualizerContainerRef = useRef<HTMLDivElement | null>(null);
    const [wavesurfer, setWavesurfer] = useState<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);
    const [currentTime, setCurrentTime] = useState<number>(0);
    const [duration, setDuration] = useState<number>(0);
    // containerWidth is used when calculating the container's dimensions
    const [containerWidth, setContainerWidth] = useState<number>(600);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    // Update container width when component mounts or window resizes
    useEffect(() => {
        const updateContainerWidth = () => {
            if (visualizerContainerRef.current) {
                const width = visualizerContainerRef.current.getBoundingClientRect().width;
                setContainerWidth(width);
            }
        };

        // Initial width calculation
        updateContainerWidth();

        // Update on window resize
        window.addEventListener('resize', updateContainerWidth);

        return () => {
            window.removeEventListener('resize', updateContainerWidth);
        };
    }, []);

    // Handle wavesurfer ready event
    const handleReady = (ws: WaveSurfer) => {
        setWavesurfer(ws);
        setIsLoading(false);
        setDuration(ws.getDuration());
    };

    // Toggle play/pause
    const handlePlayPause = () => {
        if (wavesurfer) {
            wavesurfer.playPause();
        }
    };

    // Format time in MM:SS format
    const formatTime = (timeInSeconds: number): string => {
        if (isNaN(timeInSeconds)) return '00:00';

        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);

        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
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
                                    <div className="flex items-center space-x-4">
                                        <Button
                                            onClick={handlePlayPause}
                                            variant="outline"
                                            size="icon"
                                            className="h-10 w-10 rounded-full"
                                            disabled={isLoading}
                                        >
                                            {isLoading ? (
                                                <svg
                                                    className="h-5 w-5 animate-spin text-gray-500"
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    fill="none"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <circle
                                                        className="opacity-25"
                                                        cx="12"
                                                        cy="12"
                                                        r="10"
                                                        stroke="currentColor"
                                                        strokeWidth="4"
                                                    ></circle>
                                                    <path
                                                        className="opacity-75"
                                                        fill="currentColor"
                                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                                    ></path>
                                                </svg>
                                            ) : isPlaying ? (
                                                <PauseIcon className="h-5 w-5" />
                                            ) : (
                                                <PlayIcon className="h-5 w-5" />
                                            )}
                                        </Button>

                                        <div className="w-full" ref={visualizerContainerRef}>
                                            <WavesurferPlayer
                                                height={75}
                                                waveColor="#D1D5DB" // Gray-300
                                                progressColor="#6366F1" // Indigo-500
                                                cursorColor="#4F46E5" // Indigo-600
                                                barWidth={2}
                                                barGap={1}
                                                barRadius={1}
                                                url={uploadData.stream_url}
                                                onReady={handleReady}
                                                onPlay={() => setIsPlaying(true)}
                                                onPause={() => setIsPlaying(false)}
                                                onTimeupdate={(ws: WaveSurfer) => setCurrentTime(ws.getCurrentTime())}
                                                onFinish={() => setIsPlaying(false)}
                                            />

                                            <div className="mt-2 flex justify-between text-xs text-gray-500">
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
