import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import { generateDynamicBreadcrumbs } from '@/lib/breadcrumb-utils';
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

    const breadcrumbs: BreadcrumbItem[] = (() => {
        const baseBreadcrumbs = generateDynamicBreadcrumbs(
            'Analysis',
            route('uploads.analysis.show', { upload: uploadData.id }),
            'Audio analysis and insights',
        );

        // Insert the track title between parent and current page
        return [
            baseBreadcrumbs[0], // Parent (Dashboard or Music Library)
            { title: uploadData.title, href: route('uploads.show', { upload: uploadData.id }) },
            baseBreadcrumbs[1], // Current page (Analysis)
        ];
    })();

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
                        <CardDescription>Get detailed insights about your audio including musical key, BPM, loudness, and more.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {!analysis_service.enabled ? (
                            <div className="py-8 text-center text-muted-foreground">
                                <BarChart3 className="mx-auto mb-4 h-12 w-12 opacity-50" />
                                <p>Audio analysis is currently disabled.</p>
                            </div>
                        ) : !analysis_service.available ? (
                            <div className="py-8 text-center text-muted-foreground">
                                <BarChart3 className="mx-auto mb-4 h-12 w-12 opacity-50" />
                                <p>Audio analysis service is currently unavailable.</p>
                                <p className="mt-2 text-sm">Please try again later.</p>
                            </div>
                        ) : uploadData.status !== 'ready' ? (
                            <div className="py-8 text-center text-muted-foreground">
                                <BarChart3 className="mx-auto mb-4 h-12 w-12 opacity-50" />
                                <p>Upload must be processed before analysis can begin.</p>
                                <p className="mt-2 text-sm">Current status: {uploadData.status}</p>
                            </div>
                        ) : (
                            <div className="py-8 text-center">
                                <BarChart3 className="mx-auto mb-4 h-12 w-12 text-chart-4" />
                                <p className="mb-4 text-muted-foreground">No analysis has been performed yet.</p>
                                <Button onClick={handleStartAnalysis} disabled={processing}>
                                    <Zap className="mr-2 h-4 w-4" />
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
                        <CardDescription>Your audio is being analyzed. You'll receive a notification when it's complete.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-center py-8">
                            <div className="flex flex-col items-center space-y-4">
                                <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-chart-4"></div>
                                <div className="text-center">
                                    <p className="text-sm font-medium">Processing audio...</p>
                                    <p className="text-xs text-muted-foreground">
                                        Started {new Date(uploadData.analysis_task.submitted_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-center">
                            <Button variant="secondary" onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="mr-2 h-4 w-4" />
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
                        <CardTitle className="flex items-center gap-2 text-chart-2">
                            <Music className="h-5 w-5" />
                            Analysis Failed
                        </CardTitle>
                        <CardDescription>The analysis could not be completed.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="rounded-lg border border-chart-2/20 bg-chart-2/10 p-4">
                            <p className="text-sm text-chart-2">
                                {uploadData.analysis_task.error_message || 'An unknown error occurred during analysis.'}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete Failed Task
                            </Button>
                            <Button variant="secondary" onClick={handleDeleteAnalysis} disabled={processing}>
                                <Trash2 className="mr-2 h-4 w-4" />
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
                {/* Brutalist Analysis Results Header */}
                <div className="neo-border neo-shadow bg-neo-black p-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-neo-white text-xl font-black tracking-wider uppercase">ANALYSIS RESULTS</h2>
                            <p className="font-bold text-chart-1 dark:text-chart-1">
                                COMPLETED {new Date(analysis.created_at).toLocaleString().toUpperCase()}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Link href={route('uploads.analysis.similar', { upload: uploadData.id })}>
                                <Button variant="secondary" size="sm" className="neo-shadow font-black uppercase">
                                    <Users className="mr-2 h-4 w-4" />
                                    FIND SIMILAR
                                </Button>
                            </Link>
                            <Button
                                variant="secondary"
                                size="sm"
                                className="neo-shadow border-red-500 font-black text-red-500 uppercase hover:bg-red-500 hover:text-white"
                                onClick={handleDeleteAnalysis}
                                disabled={processing}
                            >
                                <Trash2 className="mr-2 h-4 w-4" />
                                DESTROY
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Brutalist Analysis Metrics Grid */}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {/* Musical Key Display - Chart Color 1 (Green) */}
                    <div className="neo-border neo-shadow bg-chart-1 p-4">
                        <h4 className="text-neo-black mb-2 font-black tracking-wide uppercase">MUSICAL KEY</h4>
                        <div className="flex items-center gap-3">
                            <span className="text-neo-black font-mono text-3xl font-black">{analysis.musical_key || 'N/A'}</span>
                            {analysis.key_confidence && (
                                <div className="neo-border bg-neo-black text-neo-white px-2 py-1">
                                    <span className="font-mono text-xs">{Math.round(analysis.key_confidence * 100)}% CONF</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* BPM Display - Chart Color 2 (Pink) */}
                    <div className="neo-border neo-shadow bg-chart-2 p-4">
                        <h4 className="text-neo-white mb-2 font-black tracking-wide uppercase">BPM</h4>
                        <div className="flex items-center gap-3">
                            <span className="text-neo-white font-mono text-3xl font-black">{analysis.bpm || 'N/A'}</span>
                            {analysis.categories?.bpm && (
                                <div className="neo-border bg-neo-black text-neo-white px-2 py-1">
                                    <span className="text-xs font-black uppercase">{analysis.categories.bpm}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Loudness Display - Chart Color 4 (Blue) */}
                    <div className="neo-border neo-shadow bg-chart-4 p-4">
                        <h4 className="text-neo-white mb-2 font-black tracking-wide uppercase">LOUDNESS</h4>
                        <div className="flex items-center gap-3">
                            <span className="text-neo-white font-mono text-2xl font-black">
                                {analysis.loudness_db ? `${analysis.loudness_db.toFixed(1)}` : 'N/A'}
                            </span>
                            <span className="text-neo-white text-sm font-bold">dB</span>
                            {analysis.categories?.loudness && (
                                <div className="neo-border bg-neo-black text-neo-white px-2 py-1">
                                    <span className="text-xs font-black uppercase">{analysis.categories.loudness}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Dynamic Range - Chart Color 3 (Yellow) */}
                    <div className="neo-border neo-shadow bg-chart-3 p-4">
                        <h4 className="text-neo-black mb-2 font-black tracking-wide uppercase">DYNAMIC RANGE</h4>
                        <div className="flex items-center gap-3">
                            <span className="text-neo-black font-mono text-2xl font-black">
                                {analysis.dynamic_range_db ? `${analysis.dynamic_range_db.toFixed(1)}` : 'N/A'}
                            </span>
                            <span className="text-neo-black text-sm font-bold">dB</span>
                            {analysis.categories?.dynamic_range && (
                                <div className="neo-border bg-neo-black text-neo-white px-2 py-1">
                                    <span className="text-xs font-black uppercase">{analysis.categories.dynamic_range}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Brightness - Chart Color 1 (Green) */}
                    <div className="neo-border neo-shadow bg-chart-1 p-4">
                        <h4 className="text-neo-black mb-2 font-black tracking-wide uppercase">BRIGHTNESS</h4>
                        <div className="flex items-center gap-3">
                            <span className="text-neo-black font-mono text-2xl font-black">
                                {analysis.brightness ? `${Math.round(analysis.brightness)}` : 'N/A'}
                            </span>
                            <span className="text-neo-black text-sm font-bold">Hz</span>
                            {analysis.categories?.brightness && (
                                <div className="neo-border bg-neo-black text-neo-white px-2 py-1">
                                    <span className="text-xs font-black uppercase">{analysis.categories.brightness}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Beat Regularity - Chart Color 2 (Pink) */}
                    <div className="neo-border neo-shadow bg-chart-2 p-4">
                        <h4 className="text-neo-white mb-2 font-black tracking-wide uppercase">BEAT REGULARITY</h4>
                        <div className="flex items-center gap-3">
                            <span className="text-neo-white font-mono text-2xl font-black">
                                {analysis.beat_regularity ? `${Math.round(analysis.beat_regularity * 100)}` : 'N/A'}
                            </span>
                            <span className="text-neo-white text-sm font-bold">%</span>
                        </div>
                    </div>
                </div>

                {/* Additional Info - Brutalist Style */}
                {(analysis.timbral_complexity || analysis.key_changes || analysis.analysis_duration) && (
                    <div className="neo-border neo-shadow bg-neo-black p-6">
                        <h4 className="text-neo-white neo-border-b mb-4 pb-2 font-black tracking-wide uppercase">TECHNICAL DATA</h4>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            {analysis.timbral_complexity && (
                                <div className="neo-border bg-chart-3 p-3">
                                    <span className="text-neo-black block text-xs font-black uppercase">TIMBRAL COMPLEXITY</span>
                                    <span className="text-neo-black font-mono text-lg font-black">{analysis.timbral_complexity.toFixed(2)}</span>
                                </div>
                            )}
                            {analysis.key_changes && (
                                <div className="neo-border bg-chart-1 p-3">
                                    <span className="text-neo-black block text-xs font-black uppercase">KEY CHANGES</span>
                                    <span className="text-neo-black font-mono text-lg font-black">{analysis.key_changes}</span>
                                </div>
                            )}
                            {analysis.analysis_duration && (
                                <div className="neo-border bg-chart-4 p-3">
                                    <span className="text-neo-white block text-xs font-black uppercase">PROCESSING TIME</span>
                                    <span className="text-neo-white font-mono text-lg font-black">{analysis.analysis_duration.toFixed(1)}s</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Analysis - ${uploadData.title}`} />
            <div className="space-y-6 p-4 sm:p-6 lg:p-8">
                {renderAnalysisStatus()}
                {renderAnalysisResults()}
            </div>
        </AppLayout>
    );
}
