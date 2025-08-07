import { MusicCard } from '@/components/music-library-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, usePage } from '@inertiajs/react';
import { ArrowLeft, BarChart3, Music, Users } from 'lucide-react';
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

    const breadcrumbs: BreadcrumbItem[] = [
        {
            title: 'Music Library',
            href: route('uploads.index'),
        },
        {
            title: upload.title,
            href: route('uploads.show', { upload: upload.id }),
        },
        {
            title: 'Analysis',
            href: route('uploads.analysis.show', { upload: upload.id }),
        },
        {
            title: 'Similar Tracks',
            href: route('uploads.analysis.similar', { upload: upload.id }),
            description: `Found ${similar_uploads.length} similar tracks based on musical analysis`,
        },
    ];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Similar Tracks - ${upload.title}`} />
            <div className="p-4 sm:p-6 lg:p-8 space-y-6">
                {/* Back Button */}
                <div className="flex items-center gap-4">
                    <Link href={route('uploads.analysis.show', { upload: upload.id })}>
                        <Button variant="outline" size="sm">
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back to Analysis
                        </Button>
                    </Link>
                </div>

                {/* Analysis Criteria */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BarChart3 className="h-5 w-5" />
                            Search Criteria
                        </CardTitle>
                        <CardDescription>
                            Tracks similar to "{upload.title}" based on the following characteristics:
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-wrap gap-4">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">Key:</span>
                                <Badge variant={analysis_criteria.key_confidence > 0.8 ? 'default' : 'secondary'}>
                                    {analysis_criteria.musical_key}
                                </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">BPM:</span>
                                <Badge variant="outline">
                                    {analysis_criteria.bpm} ±10
                                </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">Brightness:</span>
                                <Badge variant="outline">
                                    {Math.round(analysis_criteria.brightness)} Hz ±20%
                                </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">Key Confidence:</span>
                                <Badge variant="outline">
                                    {Math.round(analysis_criteria.key_confidence * 100)}%
                                </Badge>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Results */}
                {similar_uploads.length === 0 ? (
                    <Card>
                        <CardContent className="py-12">
                            <div className="text-center">
                                <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                                <h3 className="text-lg font-semibold mb-2">No Similar Tracks Found</h3>
                                <p className="text-muted-foreground max-w-md mx-auto">
                                    We couldn't find any tracks in your library that match the musical characteristics 
                                    of "{upload.title}". Try uploading more music to build a larger collection for comparison.
                                </p>
                                <div className="mt-6">
                                    <Link href={route('uploads.create')}>
                                        <Button>
                                            <Music className="h-4 w-4 mr-2" />
                                            Upload More Music
                                        </Button>
                                    </Link>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Users className="h-5 w-5" />
                                Similar Tracks ({similar_uploads.length})
                            </CardTitle>
                            <CardDescription>
                                Tracks with similar musical characteristics, sorted by closest BPM match
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                                {similar_uploads.map((similarUpload, index) => (
                                    <div key={similarUpload.id} className="relative">
                                        <MusicCard 
                                            upload={similarUpload} 
                                            isLast={index === similar_uploads.length - 1}
                                        />
                                        {/* Show analysis comparison if available */}
                                        {similarUpload.analysis && (
                                            <div className="mt-2 p-2 bg-muted/50 rounded-lg text-xs">
                                                <div className="flex justify-between items-center">
                                                    <span className="font-medium">Analysis Match:</span>
                                                    <div className="flex gap-1">
                                                        {similarUpload.analysis.musical_key === analysis_criteria.musical_key && (
                                                            <Badge variant="outline" className="text-xs">Same Key</Badge>
                                                        )}
                                                        {similarUpload.analysis.bpm && Math.abs(similarUpload.analysis.bpm - analysis_criteria.bpm) <= 10 && (
                                                            <Badge variant="outline" className="text-xs">Similar BPM</Badge>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="mt-1 text-muted-foreground">
                                                    {similarUpload.analysis.musical_key} • {similarUpload.analysis.bpm || 'Unknown'} BPM
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Actions */}
                <Card>
                    <CardContent className="py-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h4 className="font-semibold">Discover More</h4>
                                <p className="text-sm text-muted-foreground">
                                    Upload more tracks to improve similarity matching
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <Link href={route('uploads.create')}>
                                    <Button variant="outline">
                                        <Music className="h-4 w-4 mr-2" />
                                        Upload Music
                                    </Button>
                                </Link>
                                <Link href={route('uploads.index')}>
                                    <Button>
                                        Browse Library
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </AppLayout>
    );
}