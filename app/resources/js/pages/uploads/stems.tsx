import { MultiTrackStemPlayer } from '@/components/multi-track-stem-player';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import { generateDynamicBreadcrumbs } from '@/lib/breadcrumb-utils';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, useForm, usePage } from '@inertiajs/react';
import { Download, Music, Scissors, Trash2, Zap } from 'lucide-react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface Props {
    upload: Upload;
    analysis_service: {
        enabled: boolean;
        available: boolean;
    };
}

interface Stem {
    id: number;
    stem_type: string;
    file_path: string;
    public_path?: string;
    storage_type: string;
    file_size?: number;
    duration?: number;
    formatted_file_size?: string;
    formatted_duration?: string;
    stem_type_name?: string;
}

export default function StemSeparation({ upload, analysis_service }: Props) {
    const { props } = usePage();
    const flash = props.flash as { success?: string; error?: string } | undefined;
    const uploadData = 'data' in upload && upload.data ? (upload.data as Upload) : upload;

    const { post, delete: destroy, processing } = useForm();

    useEffect(() => {
        if (flash?.success) {
            toast.success(flash.success);
        }
        if (flash?.error) {
            toast.error(flash.error);
        }
    }, [flash]);

    const breadcrumbs: BreadcrumbItem[] = (() => {
        const baseBreadcrumbs = generateDynamicBreadcrumbs(
            'Stem Separation',
            route('uploads.stems.show', { upload: uploadData.id }),
            'Separate audio into individual stems',
        );

        // Insert the track title between parent and current page
        return [
            baseBreadcrumbs[0], // Parent (Dashboard or Music Library)
            { title: uploadData.title, href: route('uploads.show', { upload: uploadData.id }) },
            baseBreadcrumbs[1], // Current page (Stem Separation)
        ];
    })();

    const handleStartSeparation = () => {
        post(route('uploads.stems.store', { upload: uploadData.id }));
    };

    const handleDeleteStems = () => {
        if (confirm('Are you sure you want to delete the stem separation data? This action cannot be undone.')) {
            destroy(route('uploads.stems.destroy', { upload: uploadData.id }));
        }
    };

    const handleDeleteTask = () => {
        if (
            confirm(
                'Are you sure you want to cancel and delete this stem separation task? This will stop the separation and allow you to start a new one.',
            )
        ) {
            destroy(route('uploads.stems.delete-task', { upload: uploadData.id }));
        }
    };

    const handleDownloadStem = (stemType: string) => {
        window.location.href = route('uploads.stems.download', {
            upload: uploadData.id,
            stemType: stemType,
        });
    };

    const getStemIcon = (stemType: string) => {
        switch (stemType) {
            case 'vocals':
                return '🎤';
            case 'drums':
                return '🥁';
            case 'bass':
                return '🎸';
            case 'other':
                return '🎹';
            default:
                return '🎵';
        }
    };

    const renderSeparationStatus = () => {
        if (!uploadData.stem_task || uploadData.stem_task.status === 'deleted') {
            return (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Scissors className="h-5 w-5" />
                            Stem Separation
                        </CardTitle>
                        <CardDescription>Separate your audio into individual stems (vocals, drums, bass, and other instruments).</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {!analysis_service.enabled ? (
                            <div className="py-8 text-center text-muted-foreground">
                                <Scissors className="mx-auto mb-4 h-12 w-12 opacity-50" />
                                <p>Audio analysis service is currently disabled.</p>
                            </div>
                        ) : !analysis_service.available ? (
                            <div className="py-8 text-center text-muted-foreground">
                                <Scissors className="mx-auto mb-4 h-12 w-12 opacity-50" />
                                <p>Audio analysis service is currently unavailable.</p>
                                <p className="mt-2 text-sm">Please try again later.</p>
                            </div>
                        ) : uploadData.status !== 'ready' ? (
                            <div className="py-8 text-center text-muted-foreground">
                                <Scissors className="mx-auto mb-4 h-12 w-12 opacity-50" />
                                <p>Upload must be processed before stem separation can begin.</p>
                                <p className="mt-2 text-sm">Current status: {uploadData.status}</p>
                            </div>
                        ) : (
                            <div className="py-8 text-center">
                                <Scissors className="mx-auto mb-4 h-12 w-12 text-[--amber]" />
                                <p className="mb-4 text-muted-foreground">No stem separation has been performed yet.</p>
                                <Button onClick={handleStartSeparation} disabled={processing}>
                                    <Zap className="mr-2 h-4 w-4" />
                                    Start Stem Separation
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            );
        }

        if (uploadData.stem_task.status === 'processing' || uploadData.stem_task.status === 'pending') {
            return (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Scissors className="h-5 w-5" />
                            Stem Separation in Progress
                        </CardTitle>
                        <CardDescription>Your audio is being separated into stems. You'll receive a notification when it's complete.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-center py-8">
                            <div className="flex flex-col items-center space-y-4">
                                <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-[--amber]"></div>
                                <div className="text-center">
                                    <p className="text-sm font-medium">Separating stems...</p>
                                    <p className="text-xs text-muted-foreground">
                                        Started {new Date(uploadData.stem_task.submitted_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-center">
                            <Button variant="secondary" onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="mr-2 h-4 w-4" />
                                Cancel Separation
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            );
        }

        if (uploadData.stem_task.status === 'failed') {
            return (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-red-600">
                            <Scissors className="h-5 w-5" />
                            Stem Separation Failed
                        </CardTitle>
                        <CardDescription>The stem separation could not be completed.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                            <p className="text-sm text-red-700">
                                {uploadData.stem_task.error_message || 'An unknown error occurred during stem separation.'}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete Failed Task
                            </Button>
                            <Button variant="secondary" onClick={handleDeleteStems} disabled={processing}>
                                <Trash2 className="mr-2 h-4 w-4" />
                                Clear All Data
                            </Button>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Delete the failed task to start a new separation, or clear all data to remove everything.
                        </p>
                    </CardContent>
                </Card>
            );
        }

        return null;
    };

    const renderStemResults = () => {
        if (!uploadData.stems || !Array.isArray(uploadData.stems) || uploadData.stems.length === 0) return null;

        const stems = uploadData.stems as Stem[];

        return (
            <div className="space-y-6">
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-2">
                                    <Music className="h-5 w-5" />
                                    Separated Stems
                                </CardTitle>
                                <CardDescription>Completed {new Date(uploadData.stem_task?.completed_at || '').toLocaleString()}</CardDescription>
                            </div>
                            <Button variant="secondary" size="sm" onClick={handleDeleteStems} disabled={processing}>
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Multi-track Stem Player */}
                        <MultiTrackStemPlayer stems={stems} uploadId={uploadData.id} analysis={uploadData.analysis || undefined} />

                        {/* Stem Downloads */}
                        <Card className="border border-[--border] bg-[--surface-2]">
                            <CardHeader className="pb-4">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2 text-foreground">
                                        <Download className="h-5 w-5" />
                                        Download Stems
                                    </CardTitle>
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <span>Total: {stems.length} files</span>
                                        <Badge variant="secondary">
                                            {stems[0]?.storage_type?.toUpperCase() || 'LOCAL'}
                                        </Badge>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {stems.map((stem) => {
                                    const getStemColor = (stemType: string) => {
                                        switch (stemType) {
                                            case 'vocals':
                                                return 'bg-blue-500/20 dark:bg-blue-500/20 border-blue-200 dark:border-blue-800';
                                            case 'drums':
                                                return 'bg-red-500/20 dark:bg-red-500/20 border-red-200 dark:border-red-800';
                                            case 'bass':
                                                return 'bg-yellow-500/20 dark:bg-yellow-500/20 border-yellow-200 dark:border-yellow-800';
                                            case 'other':
                                                return 'bg-green-500/20 dark:bg-green-500/20 border-green-200 dark:border-green-800';
                                            default:
                                                return 'bg-purple-500/20 dark:bg-purple-500/20 border-purple-200 dark:border-purple-800';
                                        }
                                    };

                                    return (
                                        <div
                                            key={stem.id}
                                            className={`flex items-center justify-between rounded-[--radius-md] border p-4 transition-all hover:shadow-sm-studio ${getStemColor(stem.stem_type)}`}
                                        >
                                            <div className="flex items-center gap-4">
                                                {/* Icon and Name */}
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xl">{getStemIcon(stem.stem_type)}</span>
                                                    <div>
                                                        <h4 className="font-semibold text-foreground">
                                                            {stem.stem_type_name || stem.stem_type.charAt(0).toUpperCase() + stem.stem_type.slice(1)}
                                                        </h4>
                                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                            {stem.formatted_file_size && <span>{stem.formatted_file_size}</span>}
                                                            {stem.formatted_file_size && stem.formatted_duration && <span>•</span>}
                                                            {stem.formatted_duration && <span>{stem.formatted_duration}</span>}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Download Button */}
                                            <Button
                                                size="sm"
                                                onClick={() => handleDownloadStem(stem.stem_type)}
                                                disabled={processing}
                                                className=""
                                            >
                                                <Download className="mr-2 h-4 w-4" />
                                                Download
                                            </Button>
                                        </div>
                                    );
                                })}
                            </CardContent>
                        </Card>

                        {/* Additional Info */}
                        <div className="mt-6 border-t border-[--border] pt-6">
                            <div className="grid grid-cols-1 gap-4 text-sm text-muted-foreground md:grid-cols-2">
                                <div>
                                    <span className="font-medium text-foreground">Total stems:</span> {stems.length}
                                </div>
                                <div>
                                    <span className="font-medium text-foreground">Storage:</span>{' '}
                                    {stems[0]?.storage_type?.toUpperCase() || 'Unknown'}
                                </div>
                                <div>
                                    <span className="font-medium text-foreground">Completed:</span>{' '}
                                    {new Date(uploadData.stem_task?.completed_at || '').toLocaleString()}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Stem Separation - ${uploadData.title}`} />
            <div className="space-y-6 p-4 sm:p-6 lg:p-8">
                {renderSeparationStatus()}
                {renderStemResults()}
            </div>
        </AppLayout>
    );
}
