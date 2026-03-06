import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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

        return [
            baseBreadcrumbs[0],
            { title: uploadData.title, href: route('uploads.show', { upload: uploadData.id }) },
            baseBreadcrumbs[1],
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

    const renderAnalysisStatus = () => {
        if (!uploadData.analysis_task || uploadData.analysis_task.status === 'deleted') {
            return (
                <div className="studio-card p-8">
                    <div className="flex items-start gap-4 mb-6">
                        <div className="flex h-10 w-10 items-center justify-center rounded-[--radius-md] bg-[--amber]/10 shrink-0">
                            <Music className="h-5 w-5 text-[--amber]" />
                        </div>
                        <div>
                            <h3 className="font-sans font-semibold text-base text-foreground mb-1">Audio analysis</h3>
                            <p className="text-sm text-muted-foreground">Get detailed insights about your audio including musical key, BPM, loudness, and more.</p>
                        </div>
                    </div>
                    {!analysis_service.enabled ? (
                        <div className="py-8 text-center text-muted-foreground">
                            <BarChart3 className="mx-auto mb-4 h-10 w-10 opacity-40" />
                            <p className="text-sm">Audio analysis is currently disabled.</p>
                        </div>
                    ) : !analysis_service.available ? (
                        <div className="py-8 text-center text-muted-foreground">
                            <BarChart3 className="mx-auto mb-4 h-10 w-10 opacity-40" />
                            <p className="text-sm">Audio analysis service is currently unavailable.</p>
                            <p className="mt-1 text-xs">Please try again later.</p>
                        </div>
                    ) : uploadData.status !== 'ready' ? (
                        <div className="py-8 text-center text-muted-foreground">
                            <BarChart3 className="mx-auto mb-4 h-10 w-10 opacity-40" />
                            <p className="text-sm">Upload must be processed before analysis can begin.</p>
                            <p className="mt-1 text-xs">Current status: {uploadData.status}</p>
                        </div>
                    ) : (
                        <div className="py-8 text-center">
                            <BarChart3 className="mx-auto mb-4 h-10 w-10 text-[--amber]" />
                            <p className="mb-5 text-sm text-muted-foreground">No analysis has been run yet.</p>
                            <Button onClick={handleStartAnalysis} disabled={processing}>
                                <Zap className="mr-2 h-4 w-4" />
                                Start analysis
                            </Button>
                        </div>
                    )}
                </div>
            );
        }

        if (uploadData.analysis_task.status === 'processing' || uploadData.analysis_task.status === 'pending') {
            return (
                <div className="studio-card p-8">
                    <div className="flex items-start gap-4 mb-6">
                        <div className="flex h-10 w-10 items-center justify-center rounded-[--radius-md] bg-[--amber]/10 shrink-0">
                            <Music className="h-5 w-5 text-[--amber]" />
                        </div>
                        <div>
                            <h3 className="font-sans font-semibold text-base text-foreground mb-1">Analysis in progress</h3>
                            <p className="text-sm text-muted-foreground">Your audio is being analyzed. You'll receive a notification when it's complete.</p>
                        </div>
                    </div>
                    <div className="flex items-center justify-center py-8">
                        <div className="flex flex-col items-center gap-4">
                            <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-[--amber]"></div>
                            <div className="text-center">
                                <p className="text-sm font-medium text-foreground">Processing audio...</p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                    Started {new Date(uploadData.analysis_task.submitted_at).toLocaleString()}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-center">
                        <Button variant="secondary" onClick={handleDeleteTask} disabled={processing}>
                            <Trash2 className="mr-2 h-4 w-4" />
                            Cancel analysis
                        </Button>
                    </div>
                </div>
            );
        }

        if (uploadData.analysis_task.status === 'failed') {
            return (
                <div className="studio-card p-8">
                    <div className="flex items-start gap-4 mb-6">
                        <div className="flex h-10 w-10 items-center justify-center rounded-[--radius-md] bg-destructive/10 shrink-0">
                            <Music className="h-5 w-5 text-destructive" />
                        </div>
                        <div>
                            <h3 className="font-sans font-semibold text-base text-destructive mb-1">Analysis failed</h3>
                            <p className="text-sm text-muted-foreground">The analysis could not be completed.</p>
                        </div>
                    </div>
                    <div className="rounded-[--radius-md] border border-destructive/20 bg-destructive/5 p-4 mb-5">
                        <p className="text-sm text-destructive">
                            {uploadData.analysis_task.error_message || 'An unknown error occurred during analysis.'}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button onClick={handleDeleteTask} disabled={processing}>
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete failed task
                        </Button>
                        <Button variant="secondary" onClick={handleDeleteAnalysis} disabled={processing}>
                            <Trash2 className="mr-2 h-4 w-4" />
                            Clear all data
                        </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-3">
                        Delete the failed task to start a new analysis, or clear all data to remove everything.
                    </p>
                </div>
            );
        }

        return null;
    };

    const renderMetricCard = (
        label: string,
        value: string,
        unit: string | null,
        category: string | null,
        accent: 'amber' | 'jade' | 'neutral' = 'amber',
    ) => {
        const accentClass = accent === 'amber' ? 'text-[--amber]' : accent === 'jade' ? 'text-[--jade]' : 'text-foreground';
        const bgClass = accent === 'amber' ? 'bg-[--amber]/10' : accent === 'jade' ? 'bg-[--jade]/10' : 'bg-[--surface-2]';
        return (
            <div className="studio-card p-5">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">{label}</p>
                <div className="flex items-baseline gap-1.5">
                    <span className={`font-mono text-3xl font-medium ${accentClass}`}>{value}</span>
                    {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
                </div>
                {category && (
                    <div className="mt-3">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${bgClass} ${accentClass}`}>
                            {category}
                        </span>
                    </div>
                )}
            </div>
        );
    };

    const renderAnalysisResults = () => {
        if (!uploadData.analysis) return null;

        const analysis = uploadData.analysis;

        return (
            <div className="space-y-6">
                {/* Results header */}
                <div className="studio-card p-5 flex items-center justify-between">
                    <div>
                        <h2 className="font-sans font-semibold text-base text-foreground mb-0.5">Analysis results</h2>
                        <p className="text-xs text-muted-foreground">
                            Completed {new Date(analysis.created_at).toLocaleString()}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link href={route('uploads.analysis.similar', { upload: uploadData.id })}>
                            <Button variant="secondary" size="sm">
                                <Users className="mr-2 h-3.5 w-3.5" />
                                Find similar
                            </Button>
                        </Link>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                            onClick={handleDeleteAnalysis}
                            disabled={processing}
                        >
                            <Trash2 className="mr-2 h-3.5 w-3.5" />
                            Delete
                        </Button>
                    </div>
                </div>

                {/* Metrics grid */}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {renderMetricCard(
                        'Musical key',
                        analysis.musical_key || 'N/A',
                        null,
                        analysis.key_confidence ? `${Math.round(analysis.key_confidence * 100)}% confidence` : null,
                        'jade',
                    )}
                    {renderMetricCard(
                        'BPM',
                        analysis.bpm ? String(analysis.bpm) : 'N/A',
                        null,
                        analysis.categories?.bpm || null,
                        'amber',
                    )}
                    {renderMetricCard(
                        'Loudness',
                        analysis.loudness_db ? analysis.loudness_db.toFixed(1) : 'N/A',
                        'dB',
                        analysis.categories?.loudness || null,
                        'neutral',
                    )}
                    {renderMetricCard(
                        'Dynamic range',
                        analysis.dynamic_range_db ? analysis.dynamic_range_db.toFixed(1) : 'N/A',
                        'dB',
                        analysis.categories?.dynamic_range || null,
                        'neutral',
                    )}
                    {renderMetricCard(
                        'Brightness',
                        analysis.brightness ? String(Math.round(analysis.brightness)) : 'N/A',
                        'Hz',
                        analysis.categories?.brightness || null,
                        'neutral',
                    )}
                    {renderMetricCard(
                        'Beat regularity',
                        analysis.beat_regularity ? String(Math.round(analysis.beat_regularity * 100)) : 'N/A',
                        '%',
                        null,
                        'neutral',
                    )}
                </div>

                {/* Technical data */}
                {(analysis.timbral_complexity || analysis.key_changes || analysis.analysis_duration) && (
                    <div className="studio-card p-6">
                        <h4 className="font-sans font-semibold text-sm text-foreground mb-4 pb-3 border-b border-[--border]">
                            Technical data
                        </h4>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            {analysis.timbral_complexity && (
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Timbral complexity</p>
                                    <p className="font-mono text-lg font-medium text-foreground">{analysis.timbral_complexity.toFixed(2)}</p>
                                </div>
                            )}
                            {analysis.key_changes && (
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Key changes</p>
                                    <p className="font-mono text-lg font-medium text-foreground">{analysis.key_changes}</p>
                                </div>
                            )}
                            {analysis.analysis_duration && (
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Processing time</p>
                                    <p className="font-mono text-lg font-medium text-foreground">{analysis.analysis_duration.toFixed(1)}s</p>
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
