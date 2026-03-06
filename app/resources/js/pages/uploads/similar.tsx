import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, usePage } from '@inertiajs/react';
import { ArrowLeft, Music, Users } from 'lucide-react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface Props {
    upload: Upload;
    similar_uploads: Upload[];
    analysis_criteria: {
        musical_key: string;
        bpm: number;
        brightness: number;
        key_confidence: number;
    };
}

export default function Similar({ upload, similar_uploads, analysis_criteria }: Props) {
    const { props } = usePage();
    const flash = props.flash as { success?: string; error?: string } | undefined;

    useEffect(() => {
        if (flash?.success) {
            toast.success(flash.success);
        }
        if (flash?.error) {
            toast.error(flash.error);
        }
    }, [flash]);

    const uploadData = upload || {};

    if (!upload || !upload.id) {
        return (
            <AppLayout breadcrumbs={[]}>
                <Head title="Similar Tracks" />
                <div className="p-4">
                    <div className="studio-card p-8 text-center">
                        <p className="text-sm text-muted-foreground">Upload data not found.</p>
                    </div>
                </div>
            </AppLayout>
        );
    }

    const breadcrumbs: BreadcrumbItem[] = [
        { title: 'Music Library', href: route('uploads.index') },
        { title: uploadData.title, href: route('uploads.show', { upload: uploadData.id }) },
        { title: 'Analysis', href: route('uploads.analysis.show', { upload: uploadData.id }) },
        {
            title: 'Similar tracks',
            href: route('uploads.analysis.similar', { upload: uploadData.id }),
            description: `Found ${similar_uploads.length} similar tracks based on musical analysis`,
        },
    ];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Similar Tracks - ${uploadData.title}`} />
            <div className="space-y-6 p-4 sm:p-6 lg:p-8">
                {/* Back button */}
                <div>
                    <Link href={route('uploads.analysis.show', { upload: uploadData.id })}>
                        <Button variant="ghost" size="sm">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back to analysis
                        </Button>
                    </Link>
                </div>

                {/* Search criteria */}
                <div className="studio-card p-6">
                    <h3 className="font-sans font-semibold text-sm text-foreground mb-1">Search parameters</h3>
                    <p className="text-xs text-muted-foreground mb-5">
                        Tracks similar to &ldquo;{uploadData.title}&rdquo; based on musical characteristics
                    </p>
                    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                        <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Key</p>
                            <p className="font-mono text-lg font-medium text-[--jade]">{analysis_criteria.musical_key}</p>
                        </div>
                        <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">BPM</p>
                            <p className="font-mono text-lg font-medium text-[--amber]">{analysis_criteria.bpm}±10</p>
                        </div>
                        <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Brightness</p>
                            <p className="font-mono text-lg font-medium text-foreground">{Math.round(analysis_criteria.brightness)}Hz</p>
                        </div>
                        <div className="rounded-[--radius-md] bg-[--surface-2] p-3">
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Confidence</p>
                            <p className="font-mono text-lg font-medium text-foreground">{Math.round(analysis_criteria.key_confidence * 100)}%</p>
                        </div>
                    </div>
                </div>

                {/* Results */}
                {similar_uploads.length === 0 ? (
                    <div className="studio-card p-12 text-center">
                        <div className="w-14 h-14 rounded-full bg-[--amber]/10 flex items-center justify-center mx-auto mb-4">
                            <Users className="h-6 w-6 text-[--amber]" />
                        </div>
                        <h3 className="font-serif text-xl text-foreground mb-2">No similar tracks found</h3>
                        <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
                            No tracks in your library match the musical characteristics of &ldquo;{uploadData.title}&rdquo;.
                            Upload more music to build a larger collection.
                        </p>
                        <Link href={route('uploads.create')}>
                            <Button>
                                <Music className="mr-2 h-4 w-4" />
                                Upload more music
                            </Button>
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {/* Results header */}
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-foreground">{similar_uploads.length} matches found</p>
                            <p className="text-xs text-muted-foreground">Sorted by BPM similarity</p>
                        </div>

                        {/* Track list */}
                        <div className="studio-card overflow-hidden divide-y divide-[--border]">
                            {similar_uploads.map((similarUpload, index) => (
                                <Link
                                    key={similarUpload.id}
                                    href={route('uploads.show', { upload: similarUpload.id })}
                                    className="flex items-center gap-4 px-5 py-4 hover:bg-muted transition-colors group"
                                >
                                    {/* Index */}
                                    <span className="font-mono text-xs text-muted-foreground w-5 shrink-0">{index + 1}</span>

                                    {/* Icon */}
                                    <div className="w-10 h-10 rounded-[--radius-md] bg-[--surface-2] flex items-center justify-center shrink-0">
                                        <Music className="h-4 w-4 text-muted-foreground" />
                                    </div>

                                    {/* Info */}
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm text-foreground truncate group-hover:text-[--amber] transition-colors">
                                            {similarUpload.title}
                                        </p>
                                        {similarUpload.artist && (
                                            <p className="text-xs text-muted-foreground truncate">by {similarUpload.artist}</p>
                                        )}
                                    </div>

                                    {/* Analysis data */}
                                    {similarUpload.analysis && (
                                        <div className="flex items-center gap-3 shrink-0 text-xs text-muted-foreground">
                                            {similarUpload.analysis.musical_key && (
                                                <span className="font-mono text-[--jade]">{similarUpload.analysis.musical_key}</span>
                                            )}
                                            {similarUpload.analysis.bpm && (
                                                <span className="font-mono text-[--amber]">{similarUpload.analysis.bpm} BPM</span>
                                            )}
                                        </div>
                                    )}

                                    <Badge variant="secondary">{similarUpload.status}</Badge>
                                </Link>
                            ))}
                        </div>
                    </div>
                )}

                {/* Actions footer */}
                <div className="flex items-center justify-between pt-2">
                    <p className="text-sm text-muted-foreground">Upload more tracks to improve similarity matching</p>
                    <div className="flex gap-2">
                        <Link href={route('uploads.create')}>
                            <Button variant="secondary" size="sm">
                                <Music className="mr-2 h-4 w-4" />
                                Upload music
                            </Button>
                        </Link>
                        <Link href={route('uploads.index')}>
                            <Button variant="ghost" size="sm">Browse library</Button>
                        </Link>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
