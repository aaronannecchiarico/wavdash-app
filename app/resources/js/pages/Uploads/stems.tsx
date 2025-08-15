import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, useForm, usePage } from '@inertiajs/react';
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

    const breadcrumbs: BreadcrumbItem[] = [
        {
            title: 'Music Library',
            href: route('uploads.index'),
        },
        {
            title: uploadData.title,
            href: route('uploads.show', { upload: uploadData.id }),
        },
        {
            title: 'Stem Separation',
            href: route('uploads.stems.show', { upload: uploadData.id }),
            description: 'Separate audio into individual stems',
        },
    ];

    const handleStartSeparation = () => {
        post(route('uploads.stems.store', { upload: uploadData.id }));
    };

    const handleDeleteStems = () => {
        if (confirm('Are you sure you want to delete the stem separation data? This action cannot be undone.')) {
            destroy(route('uploads.stems.destroy', { upload: uploadData.id }));
        }
    };

    const handleDeleteTask = () => {
        if (confirm('Are you sure you want to cancel and delete this stem separation task? This will stop the separation and allow you to start a new one.')) {
            destroy(route('uploads.stems.delete-task', { upload: uploadData.id }));
        }
    };

    const handleDownloadStem = (stemType: string) => {
        window.location.href = route('uploads.stems.download', { 
            upload: uploadData.id, 
            stemType: stemType 
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
                        <CardDescription>
                            Separate your audio into individual stems (vocals, drums, bass, and other instruments).
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {!analysis_service.enabled ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Scissors className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Audio analysis service is currently disabled.</p>
                            </div>
                        ) : !analysis_service.available ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Scissors className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Audio analysis service is currently unavailable.</p>
                                <p className="text-sm mt-2">Please try again later.</p>
                            </div>
                        ) : uploadData.status !== 'ready' ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Scissors className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Upload must be processed before stem separation can begin.</p>
                                <p className="text-sm mt-2">Current status: {uploadData.status}</p>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <Scissors className="h-12 w-12 mx-auto mb-4 text-blue-500" />
                                <p className="mb-4 text-muted-foreground">No stem separation has been performed yet.</p>
                                <Button onClick={handleStartSeparation} disabled={processing}>
                                    <Zap className="h-4 w-4 mr-2" />
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
                        <CardDescription>
                            Your audio is being separated into stems. You'll receive a notification when it's complete.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-center py-8">
                            <div className="flex flex-col items-center space-y-4">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                                <div className="text-center">
                                    <p className="text-sm font-medium">Separating stems...</p>
                                    <p className="text-xs text-muted-foreground">
                                        Started {new Date(uploadData.stem_task.submitted_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-center">
                            <Button variant="outline" onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="h-4 w-4 mr-2" />
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
                        <CardDescription>
                            The stem separation could not be completed.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-700">
                                {uploadData.stem_task.error_message || 'An unknown error occurred during stem separation.'}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete Failed Task
                            </Button>
                            <Button variant="outline" onClick={handleDeleteStems} disabled={processing}>
                                <Trash2 className="h-4 w-4 mr-2" />
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
                                <CardDescription>
                                    Completed {new Date(uploadData.stem_task?.completed_at || '').toLocaleString()}
                                </CardDescription>
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleDeleteStems}
                                disabled={processing}
                            >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {stems.map((stem) => (
                                <Card key={stem.id} className="border-2">
                                    <CardHeader className="pb-3">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <span className="text-2xl">{getStemIcon(stem.stem_type)}</span>
                                                <div>
                                                    <h4 className="font-semibold">
                                                        {stem.stem_type_name || stem.stem_type.charAt(0).toUpperCase() + stem.stem_type.slice(1)}
                                                    </h4>
                                                    <Badge variant="outline" className="text-xs">
                                                        {stem.storage_type.toUpperCase()}
                                                    </Badge>
                                                </div>
                                            </div>
                                            <Button
                                                size="sm"
                                                onClick={() => handleDownloadStem(stem.stem_type)}
                                                disabled={processing}
                                            >
                                                <Download className="h-4 w-4 mr-2" />
                                                Download
                                            </Button>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="pt-0">
                                        <div className="text-sm text-muted-foreground space-y-1">
                                            {stem.formatted_file_size && (
                                                <p>Size: {stem.formatted_file_size}</p>
                                            )}
                                            {stem.formatted_duration && (
                                                <p>Duration: {stem.formatted_duration}</p>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>

                        {/* Additional Info */}
                        <div className="mt-6 pt-6 border-t">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-muted-foreground">
                                <div>
                                    <span className="font-medium">Total Stems:</span> {stems.length}
                                </div>
                                <div>
                                    <span className="font-medium">Storage:</span> {stems[0]?.storage_type?.toUpperCase() || 'Unknown'}
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
            <div className="p-4 sm:p-6 lg:p-8 space-y-6">
                {renderSeparationStatus()}
                {renderStemResults()}
            </div>
        </AppLayout>
    );
}