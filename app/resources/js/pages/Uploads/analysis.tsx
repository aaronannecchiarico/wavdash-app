import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, useForm, usePage } from '@inertiajs/react';
import { BarChart3, Music, Trash2, Users, Zap } from 'lucide-react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface Props {
    upload: Upload;
    analysis_service: {
        enabled: boolean;
        available: boolean;
    };
}

export default function Analysis({ upload, analysis_service }: Props) {
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
            title: 'Analysis',
            href: route('uploads.analysis.show', { upload: uploadData.id }),
            description: 'Audio analysis and insights',
        },
    ];

    const handleStartAnalysis = () => {
        post(route('uploads.analysis.store', { upload: uploadData.id }));
    };

    const handleDeleteAnalysis = () => {
        if (confirm('Are you sure you want to delete the analysis data? This action cannot be undone.')) {
            destroy(route('uploads.analysis.destroy', { upload: uploadData.id }));
        }
    };

    const handleDeleteTask = () => {
        if (confirm('Are you sure you want to cancel and delete this analysis task? This will stop the analysis and allow you to start a new one.')) {
            destroy(route('uploads.analysis.delete-task', { upload: uploadData.id }));
        }
    };

    console.log(uploadData);

    const renderAnalysisStatus = () => {
        if (!uploadData.analysis_task || uploadData.analysis_task.status === 'deleted') {
            return (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Music className="h-5 w-5" />
                            Audio Analysis
                        </CardTitle>
                        <CardDescription>
                            Get detailed insights about your audio including musical key, BPM, loudness, and more.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {!analysis_service.enabled ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Audio analysis is currently disabled.</p>
                            </div>
                        ) : !analysis_service.available ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Audio analysis service is currently unavailable.</p>
                                <p className="text-sm mt-2">Please try again later.</p>
                            </div>
                        ) : uploadData.status !== 'ready' ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Upload must be processed before analysis can begin.</p>
                                <p className="text-sm mt-2">Current status: {uploadData.status}</p>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-blue-500" />
                                <p className="mb-4 text-muted-foreground">No analysis has been performed yet.</p>
                                <Button onClick={handleStartAnalysis} disabled={processing}>
                                    <Zap className="h-4 w-4 mr-2" />
                                    Start Analysis
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            );
        }

        if (uploadData.analysis_task.status === 'processing' || uploadData.analysis_task.status === 'pending') {
            return (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Music className="h-5 w-5" />
                            Analysis in Progress
                        </CardTitle>
                        <CardDescription>
                            Your audio is being analyzed. You'll receive a notification when it's complete.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-center py-8">
                            <div className="flex flex-col items-center space-y-4">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                                <div className="text-center">
                                    <p className="text-sm font-medium">Processing audio...</p>
                                    <p className="text-xs text-muted-foreground">
                                        Started {new Date(uploadData.analysis_task.submitted_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-center">
                            <Button variant="outline" onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Cancel Analysis
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            );
        }

        if (uploadData.analysis_task.status === 'failed') {
            return (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-red-600">
                            <Music className="h-5 w-5" />
                            Analysis Failed
                        </CardTitle>
                        <CardDescription>
                            The analysis could not be completed.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-700">
                                {uploadData.analysis_task.error_message || 'An unknown error occurred during analysis.'}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete Failed Task
                            </Button>
                            <Button variant="outline" onClick={handleDeleteAnalysis} disabled={processing}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Clear All Data
                            </Button>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Delete the failed task to start a new analysis, or clear all data to remove everything.
                        </p>
                    </CardContent>
                </Card>
            );
        }

        return null;
    };

    const renderAnalysisResults = () => {
        if (!uploadData.analysis) return null;

        const analysis = uploadData.analysis;

        return (
            <div className="space-y-6">
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-2">
                                    <BarChart3 className="h-5 w-5" />
                                    Analysis Results
                                </CardTitle>
                                <CardDescription>
                                    Completed {new Date(analysis.created_at).toLocaleString()}
                                </CardDescription>
                            </div>
                            <div className="flex gap-2">
                                <Link href={route('uploads.analysis.similar', { upload: uploadData.id })}>
                                    <Button variant="outline" size="sm">
                                        <Users className="h-4 w-4 mr-2" />
                                        Find Similar
                                    </Button>
                                </Link>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleDeleteAnalysis}
                                    disabled={processing}
                                >
                                    <Trash2 className="h-4 w-4 mr-2" />
                                    Delete
                                </Button>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {/* Musical Key */}
                            <div className="space-y-2">
                                <h4 className="font-semibold">Musical Key</h4>
                                <div className="flex items-center gap-2">
                                    <Badge variant={analysis.reliability?.has_reliable_key ? 'default' : 'secondary'}>
                                        {analysis.musical_key || 'Unknown'}
                                    </Badge>
                                    {analysis.key_confidence && (
                                        <span className="text-sm text-muted-foreground">
                                            {Math.round(analysis.key_confidence * 100)}% confidence
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* BPM */}
                            <div className="space-y-2">
                                <h4 className="font-semibold">BPM</h4>
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-mono">{analysis.bpm || 'N/A'}</span>
                                    {analysis.categories?.bpm && (
                                        <Badge variant="outline">{analysis.categories.bpm}</Badge>
                                    )}
                                </div>
                            </div>

                            {/* Loudness */}
                            <div className="space-y-2">
                                <h4 className="font-semibold">Loudness</h4>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg font-mono">
                                        {analysis.loudness_db ? `${analysis.loudness_db.toFixed(1)} dB` : 'N/A'}
                                    </span>
                                    {analysis.categories?.loudness && (
                                        <Badge variant="outline">{analysis.categories.loudness}</Badge>
                                    )}
                                </div>
                            </div>

                            {/* Dynamic Range */}
                            <div className="space-y-2">
                                <h4 className="font-semibold">Dynamic Range</h4>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg font-mono">
                                        {analysis.dynamic_range_db ? `${analysis.dynamic_range_db.toFixed(1)} dB` : 'N/A'}
                                    </span>
                                    {analysis.categories?.dynamic_range && (
                                        <Badge variant="outline">{analysis.categories.dynamic_range}</Badge>
                                    )}
                                </div>
                            </div>

                            {/* Brightness */}
                            <div className="space-y-2">
                                <h4 className="font-semibold">Brightness</h4>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg font-mono">
                                        {analysis.brightness ? `${Math.round(analysis.brightness)} Hz` : 'N/A'}
                                    </span>
                                    {analysis.categories?.brightness && (
                                        <Badge variant="outline">{analysis.categories.brightness}</Badge>
                                    )}
                                </div>
                            </div>

                            {/* Beat Regularity */}
                            <div className="space-y-2">
                                <h4 className="font-semibold">Beat Regularity</h4>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg font-mono">
                                        {analysis.beat_regularity ? `${Math.round(analysis.beat_regularity * 100)}%` : 'N/A'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Additional Info */}
                        {(analysis.timbral_complexity || analysis.key_changes || analysis.analysis_duration) && (
                            <div className="mt-6 pt-6 border-t">
                                <h4 className="font-semibold mb-3">Additional Information</h4>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                                    {analysis.timbral_complexity && (
                                        <div>
                                            <span className="font-medium">Timbral Complexity:</span>{' '}
                                            {analysis.timbral_complexity.toFixed(2)}
                                        </div>
                                    )}
                                    {analysis.key_changes && (
                                        <div>
                                            <span className="font-medium">Key Changes:</span>{' '}
                                            {analysis.key_changes}
                                        </div>
                                    )}
                                    {analysis.analysis_duration && (
                                        <div>
                                            <span className="font-medium">Processing Time:</span>{' '}
                                            {analysis.analysis_duration.toFixed(1)}s
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        );
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Analysis - ${uploadData.title}`} />
            <div className="p-4 sm:p-6 lg:p-8 space-y-6">
                {renderAnalysisStatus()}
                {renderAnalysisResults()}
            </div>
        </AppLayout>
    );
}
