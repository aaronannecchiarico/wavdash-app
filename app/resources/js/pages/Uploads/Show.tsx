import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { SoundcloudWaveform } from '@/components/soundcloud-waveform';
import AppLayout from '@/layouts/app-layout';
import { formatFileSize } from '@/lib/formatters';
import { getStatusColor } from '@/lib/upload-helpers';
import { type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import { formatDistance } from 'date-fns';
import { Loader2, PauseIcon, PencilIcon, PlayIcon, Trash2Icon as TrashIcon } from 'lucide-react';
import { useState } from 'react';
import type WaveSurfer from 'wavesurfer.js';
import { Upload } from '@/types';

interface Props {
    upload: Upload;
}

export default function Show({ upload }: Props) {
    const uploadData = 'data' in upload && upload.data ? (upload.data as Upload) : upload;
    const [wavesurfer, setWavesurfer] = useState<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const handlePlayPause = () => {
        if (wavesurfer) {
            wavesurfer.playPause();
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
                                <h3 className="mb-2 text-sm font-medium text-foreground/80 dark:text-foreground/90">Description</h3>
                                <p className="text-foreground/70 dark:text-foreground/80">{uploadData.description}</p>
                            </div>
                        )}

                        <div>
                            <h3 className="mb-2 text-sm font-medium text-foreground/80 dark:text-foreground/90">File Details</h3>
                            <dl className="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-muted-foreground">Filename</dt>
                                    <dd className="mt-1 text-sm text-foreground">{uploadData.filename}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-muted-foreground">Type</dt>
                                    <dd className="mt-1 text-sm text-foreground">{uploadData.mime_type}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-muted-foreground">Size</dt>
                                    <dd className="mt-1 text-sm text-foreground">{formatFileSize(uploadData.size)}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-muted-foreground">Last Updated</dt>
                                    <dd className="mt-1 text-sm text-foreground">
                                        {formatDistance(new Date(uploadData.updated_at), new Date(), { addSuffix: true })}
                                    </dd>
                                </div>
                            </dl>
                        </div>

                        {uploadData.status === 'ready' && uploadData.stream_url && (
                            <div>
                                <h3 className="mb-2 text-sm font-medium text-foreground/80 dark:text-foreground/90">Preview</h3>

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
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                            ) : isPlaying ? (
                                                <PauseIcon className="h-5 w-5" />
                                            ) : (
                                                <PlayIcon className="h-5 w-5" />
                                            )}
                                        </Button>

                                        <div className="w-full">
                                            <SoundcloudWaveform
                                                url={uploadData.stream_url}
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
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="flex justify-between">
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
                        >
                            <Button variant="destructive">
                                <TrashIcon className="mr-2 h-4 w-4" />
                                Delete
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>
            </div>
        </AppLayout>
    );
}
