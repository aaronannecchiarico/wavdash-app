import { AudioPlayer } from '@/components/audio-player';
import { DeleteUploadDialog } from '@/components/delete-upload-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { UploadProcessingPanel } from '@/components/upload-processing-panel';
import AppLayout from '@/layouts/app-layout';
import { formatFileSize } from '@/lib/formatters';
import { Upload, type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import { formatDistance } from 'date-fns';
import { PencilIcon, Trash2Icon as TrashIcon } from 'lucide-react';
import { useState } from 'react';

interface Props {
    upload: Upload;
}

const statusVariantMap: Record<string, 'success' | 'processing' | 'destructive' | 'warning'> = {
    ready: 'success',
    processing: 'processing',
    failed: 'destructive',
    pending: 'warning',
};

export default function Show({ upload }: Props) {
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const uploadData = 'data' in upload && upload.data ? (upload.data as Upload) : upload;
    const breadcrumbs: BreadcrumbItem[] = [
        { title: 'Music Library', href: route('uploads.index') },
        { title: uploadData.title, href: route('uploads.show', uploadData.id), description: 'View track details' },
    ];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={uploadData.title} />

            <div className="px-4 py-8 sm:px-6 lg:px-8">
                <div className="space-y-8">
                    {/* Upload header */}
                    <section className="studio-card p-6 md:p-8">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h1 className="font-serif text-2xl md:text-3xl text-foreground mb-1">
                                    {uploadData.title}
                                </h1>
                                <p className="text-sm text-muted-foreground">
                                    Uploaded {formatDistance(new Date(uploadData.created_at), new Date(), { addSuffix: true })}
                                </p>
                            </div>
                            <Badge variant={statusVariantMap[uploadData.status] || 'secondary'}>
                                {uploadData.status}
                            </Badge>
                        </div>
                    </section>

                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-5 lg:gap-10">
                        {/* Left column — primary content */}
                        <div className="lg:col-span-3 space-y-5">
                            {/* Description */}
                            {uploadData.description && (
                                <div className="studio-card p-5">
                                    <h3 className="font-sans font-semibold text-xs text-muted-foreground uppercase tracking-wide mb-2">
                                        Description
                                    </h3>
                                    <p className="text-sm text-foreground leading-relaxed">{uploadData.description}</p>
                                </div>
                            )}

                            {/* File details */}
                            <div className="studio-card p-5">
                                <h3 className="font-sans font-semibold text-xs text-muted-foreground uppercase tracking-wide mb-4">
                                    File details
                                </h3>
                                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                    <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                                        <dt className="text-xs font-medium text-muted-foreground mb-1">Filename</dt>
                                        <dd className="text-sm font-medium text-foreground truncate">{uploadData.filename}</dd>
                                    </div>
                                    <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                                        <dt className="text-xs font-medium text-muted-foreground mb-1">Type</dt>
                                        <dd className="text-sm font-medium text-foreground">{uploadData.mime_type}</dd>
                                    </div>
                                    <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                                        <dt className="text-xs font-medium text-muted-foreground mb-1">Size</dt>
                                        <dd className="font-mono text-sm font-medium text-foreground">{formatFileSize(uploadData.size)}</dd>
                                    </div>
                                    <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                                        <dt className="text-xs font-medium text-muted-foreground mb-1">Last updated</dt>
                                        <dd className="text-sm font-medium text-foreground">
                                            {formatDistance(new Date(uploadData.updated_at), new Date(), { addSuffix: true })}
                                        </dd>
                                    </div>
                                </div>
                            </div>

                            {/* Audio player */}
                            {uploadData.status === 'ready' && uploadData.stream_url && (
                                <AudioPlayer url={uploadData.stream_url} title="Main track" />
                            )}

                            {/* Actions */}
                            <div className="flex flex-wrap justify-end gap-2 pt-2">
                                <Link href={route('uploads.edit', uploadData.id)}>
                                    <Button variant="secondary">
                                        <PencilIcon className="mr-2 h-4 w-4" />
                                        Edit track
                                    </Button>
                                </Link>
                                <Button
                                    variant="ghost"
                                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                    onClick={() => setDeleteDialogOpen(true)}
                                >
                                    <TrashIcon className="mr-2 h-4 w-4" />
                                    Delete
                                </Button>
                            </div>
                        </div>

                        {/* Right column — processing panel */}
                        <div className="lg:col-span-2">
                            <div className="studio-card p-5">
                                <h2 className="font-sans font-semibold text-base text-foreground mb-5">Processing options</h2>
                                <UploadProcessingPanel upload={uploadData} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <DeleteUploadDialog upload={uploadData} isOpen={deleteDialogOpen} onOpenChange={setDeleteDialogOpen} />
        </AppLayout>
    );
}
