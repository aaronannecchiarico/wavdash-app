import { Button } from '@/components/ui/neo/button';
import { Badge } from '@/components/ui/neo/badge';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/neo/card';
import { AudioPlayer } from '@/components/audio-player.tsx';
import { DeleteUploadDialog } from '@/components/delete-upload-dialog';
import { UploadProcessingPanel } from '@/components/upload-processing-panel';
import AppLayout from '@/layouts/app-layout';
import { formatFileSize } from '@/lib/formatters';
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

    const getStatusColorNeo = (status: string) => {
        switch (status) {
            case 'ready':
                return 'bg-chart-1'; // neo-green
            case 'processing':
                return 'bg-chart-3'; // neo-yellow  
            case 'failed':
                return 'bg-red-500';
            default:
                return 'bg-chart-4'; // neo-blue
        }
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={uploadData.title} />

            <div className="py-8 px-4 sm:px-6 lg:pl-6 lg:pr-8">
                <div className="space-y-8">
                    {/* Upload header with color block */}
                    <section className="border-2 border-border p-8 transition-all hover:translate-x-1 hover:translate-y-1 bg-chart-2" style={{ boxShadow: 'var(--shadow)' }}>
                        <div className="flex justify-between items-start">
                            <div>
                                <h1 className="text-3xl font-heading font-black uppercase tracking-wider text-main-foreground mb-2">
                                    {uploadData.title}
                                </h1>
                                <p className="text-lg font-base font-bold text-main-foreground opacity-80">
                                    UPLOADED {formatDistance(new Date(uploadData.created_at), new Date(), { addSuffix: true }).toUpperCase()}
                                </p>
                            </div>
                            <Badge className={`${getStatusColorNeo(uploadData.status)} font-heading font-black uppercase tracking-wider`}>
                                {uploadData.status.toUpperCase()}
                            </Badge>
                        </div>
                    </section>

                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 lg:gap-16">
                        {/* Left Column - Primary Content */}
                        <div className="lg:col-span-3 lg:pr-8">
                            <Card className="transition-all hover:translate-x-1 hover:translate-y-1">
                                <CardHeader className="bg-secondary-background">
                                    <CardTitle className="font-heading font-black uppercase tracking-wider text-main-foreground">
                                        TRACK DETAILS
                                    </CardTitle>
                                </CardHeader>

                                <CardContent className="space-y-6">
                                    {uploadData.description && (
                                        <div className="border-2 border-border bg-background p-4">
                                            <h3 className="mb-2 text-sm font-heading font-black uppercase tracking-wider text-foreground">DESCRIPTION</h3>
                                            <p className="font-base font-bold text-foreground">{uploadData.description}</p>
                                        </div>
                                    )}

                                    <div className="border-2 border-border bg-background p-4">
                                        <h3 className="mb-4 text-sm font-heading font-black uppercase tracking-wider text-foreground">FILE DETAILS</h3>
                                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                                            <div className="border-2 border-border bg-chart-1 p-3">
                                                <dt className="text-xs font-heading font-black uppercase text-main-foreground">FILENAME</dt>
                                                <dd className="mt-1 font-base font-bold text-main-foreground">{uploadData.filename}</dd>
                                            </div>
                                            <div className="border-2 border-border bg-chart-2 p-3">
                                                <dt className="text-xs font-heading font-black uppercase text-main-foreground">TYPE</dt>
                                                <dd className="mt-1 font-base font-bold text-main-foreground">{uploadData.mime_type}</dd>
                                            </div>
                                            <div className="border-2 border-border bg-chart-3 p-3">
                                                <dt className="text-xs font-heading font-black uppercase text-main-foreground">SIZE</dt>
                                                <dd className="mt-1 font-base font-bold text-main-foreground">{formatFileSize(uploadData.size)}</dd>
                                            </div>
                                            <div className="border-2 border-border bg-chart-4 p-3">
                                                <dt className="text-xs font-heading font-black uppercase text-main-foreground">LAST UPDATED</dt>
                                                <dd className="mt-1 font-base font-bold text-main-foreground">
                                                    {formatDistance(new Date(uploadData.updated_at), new Date(), { addSuffix: true }).toUpperCase()}
                                                </dd>
                                            </div>
                                        </div>
                                    </div>

                                    {uploadData.status === 'ready' && uploadData.stream_url && (
                                        <div className="border-2 border-border bg-background p-4">
                                            <h3 className="mb-4 text-sm font-heading font-black uppercase tracking-wider text-foreground">MAIN TRACK</h3>
                                            <AudioPlayer
                                                url={uploadData.stream_url}
                                                title="MAIN TRACK"
                                                className="mb-4"
                                            />
                                        </div>
                                    )}
                                </CardContent>

                                <CardFooter className="bg-border border-t-2 border-border flex flex-wrap gap-4 justify-between">
                                    <div className="text-xs font-base text-foreground uppercase">
                                        ACTIONS
                                    </div>
                                    <div className="flex gap-2">
                                        <Link href={route('uploads.edit', uploadData.id)}>
                                            <Button variant="neutral" className="font-heading font-black uppercase tracking-wider">
                                                <PencilIcon className="mr-2 h-4 w-4" />
                                                EDIT TRACK
                                            </Button>
                                        </Link>

                                        <Button 
                                            className="bg-red-500 text-white font-heading font-black uppercase tracking-wider hover:bg-red-600" 
                                            onClick={handleDeleteClick}
                                        >
                                            <TrashIcon className="mr-2 h-4 w-4" />
                                            DESTROY
                                        </Button>
                                    </div>
                                </CardFooter>
                            </Card>
                        </div>

                        {/* Right Column - Processing Panel */}
                        <div className="lg:col-span-2 lg:pl-8">
                            <div className="border-2 border-border bg-background p-6 transition-all hover:translate-x-1 hover:translate-y-1" style={{ boxShadow: 'var(--shadow)' }}>
                                <h2 className="text-2xl font-heading font-black uppercase tracking-wide mb-6 text-foreground">
                                    PROCESSING OPTIONS
                                </h2>
                                <UploadProcessingPanel upload={uploadData} />
                            </div>
                        </div>
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
