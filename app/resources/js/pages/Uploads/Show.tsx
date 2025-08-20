import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { AudioPlayer } from '@/components/audio-player';
import { DeleteUploadDialog } from '@/components/delete-upload-dialog';
import { UploadProcessingPanel } from '@/components/upload-processing-panel';
import AppLayout from '@/layouts/app-layout';
import { formatFileSize } from '@/lib/formatters';
import { getStatusColor } from '@/lib/upload-helpers';
import { type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import { formatDistance } from 'date-fns';
import { PencilIcon, Trash2Icon as TrashIcon } from 'lucide-react';
import { Upload } from '@/types';
import { useState } from 'react';

interface Props {
    upload: Upload;
}

export default function Show({ upload }: Props) {
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const uploadData = 'data' in upload && upload.data ? (upload.data as Upload) : upload;
    const breadcrumbs: BreadcrumbItem[] = [
        { title: 'Music Library', href: route('uploads.index') },
        { title: uploadData.title, href: route('uploads.show', uploadData.id), description: 'View track details' },
    ];

    const handleDeleteClick = () => {
        setDeleteDialogOpen(true);
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={uploadData.title} />

            {/* Desktop: Two-column layout, Mobile: Single column */}
            <div className="py-8 px-4 sm:px-6 lg:pl-6 lg:pr-8">
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 lg:gap-16">
                    {/* Left Column - Primary Content (Desktop: 3/5 width, Mobile: Full width) */}
                    <div className="lg:col-span-3 lg:pr-8">
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
                                        <h3 className="mb-2 text-sm font-medium text-foreground/80 dark:text-foreground/90">Audio Preview</h3>
                                        <AudioPlayer
                                            url={uploadData.stream_url}
                                            title="Preview"
                                            className="mb-4"
                                        />
                                    </div>
                                )}
                            </CardContent>

                            <CardFooter className="flex flex-wrap gap-2 justify-end">
                                <Link href={route('uploads.edit', uploadData.id)}>
                                    <Button variant="outline">
                                        <PencilIcon className="mr-2 h-4 w-4" />
                                        Edit
                                    </Button>
                                </Link>

                                <Button variant="destructive" onClick={handleDeleteClick}>
                                    <TrashIcon className="mr-2 h-4 w-4" />
                                    Delete
                                </Button>
                            </CardFooter>
                        </Card>
                    </div>

                    {/* Right Column - Processing Panel (Desktop: 2/5 width, Mobile: Full width below left column) */}
                    <div className="lg:col-span-2 lg:pl-8">
                        <UploadProcessingPanel upload={uploadData} />
                    </div>
                </div>
            </div>

            {/* Delete Confirmation Dialog */}
            <DeleteUploadDialog
                upload={uploadData}
                isOpen={deleteDialogOpen}
                onOpenChange={setDeleteDialogOpen}
            />
        </AppLayout>
    );
}
