import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { AudioPlayer } from '@/components/audio-player';
import AppLayout from '@/layouts/app-layout';
import { formatFileSize } from '@/lib/formatters';
import { getStatusColor } from '@/lib/upload-helpers';
import { type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import { formatDistance } from 'date-fns';
import { BarChart3, PencilIcon, Scissors, Trash2Icon as TrashIcon } from 'lucide-react';
import { Upload } from '@/types';

interface Props {
    upload: Upload;
}

export default function Show({ upload }: Props) {
    const uploadData = 'data' in upload && upload.data ? (upload.data as Upload) : upload;
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
                            <AudioPlayer
                                url={uploadData.stream_url}
                                title="Preview"
                                className="mb-4"
                            />
                        )}
                    </CardContent>

                    <CardFooter className="flex flex-wrap gap-2 justify-between">
                        <div className="flex flex-wrap gap-2">
                            <Link href={route('uploads.analysis.show', uploadData.id)}>
                                <Button variant="outline" className="flex items-center">
                                    <BarChart3 className="mr-2 h-4 w-4" />
                                    Analysis
                                    {uploadData.has_analysis && (
                                        <Badge variant="secondary" className="ml-2 text-xs">
                                            Done
                                        </Badge>
                                    )}
                                    {uploadData.is_analysis_in_progress && (
                                        <Badge variant="outline" className="ml-2 text-xs">
                                            Processing
                                        </Badge>
                                    )}
                                </Button>
                            </Link>

                            <Link href={route('uploads.stems.show', uploadData.id)}>
                                <Button variant="outline" className="flex items-center">
                                    <Scissors className="mr-2 h-4 w-4" />
                                    Stem Separation
                                    {uploadData.has_stems && (
                                        <Badge variant="secondary" className="ml-2 text-xs">
                                            Done
                                        </Badge>
                                    )}
                                    {uploadData.is_stem_separation_in_progress && (
                                        <Badge variant="outline" className="ml-2 text-xs">
                                            Processing
                                        </Badge>
                                    )}
                                </Button>
                            </Link>
                        </div>

                        <div className="flex gap-2">
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
                        </div>
                    </CardFooter>
                </Card>
            </div>
        </AppLayout>
    );
}
