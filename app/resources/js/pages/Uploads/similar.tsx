import { BrutalistSimilarTrackCard } from '@/components/brutalist-similar-track-card';
import { Button } from '@/components/ui/neo/button';
import { Badge } from '@/components/ui/neo/badge';
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

    // Ensure we have proper upload data with safety checks
    const uploadData = upload || {};
    
    // Early return if no upload data
    if (!upload || !upload.id) {
        return (
            <AppLayout breadcrumbs={[]}>
                <Head title="Similar Tracks" />
                <div className="p-4">
                    <div className="neo-border neo-shadow bg-neo-pink p-8 text-center">
                        <p className="text-neo-white font-black uppercase">UPLOAD DATA NOT FOUND</p>
                    </div>
                </div>
            </AppLayout>
        );
    }

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
        },
        {
            title: 'Similar Tracks',
            href: route('uploads.analysis.similar', { upload: uploadData.id }),
            description: `Found ${similar_uploads.length} similar tracks based on musical analysis`,
        },
    ];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Similar Tracks - ${uploadData.title}`} />
            <div className="p-4 sm:p-6 lg:p-8 space-y-6">
                {/* Brutalist Back Button */}
                <div className="flex items-center gap-4">
                    <Link href={route('uploads.analysis.show', { upload: uploadData.id })}>
                        <Button variant="neutral" size="sm" className="font-black uppercase neo-shadow">
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            BACK TO ANALYSIS
                        </Button>
                    </Link>
                </div>

                {/* Brutalist Search Criteria Display */}
                <div className="neo-border neo-shadow bg-neo-yellow p-6">
                    <h3 className="font-black uppercase tracking-widest text-neo-black mb-4">
                        SEARCH PARAMETERS
                    </h3>
                    <p className="font-bold text-neo-black mb-6 text-sm">
                        TRACKS SIMILAR TO "{uploadData.title.toUpperCase()}" BASED ON MUSICAL CHARACTERISTICS
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="neo-border bg-neo-black p-3">
                            <span className="block text-xs font-black uppercase text-neo-white">KEY</span>
                            <span className="text-lg font-black text-neo-green">
                                {analysis_criteria.musical_key}
                            </span>
                        </div>
                        <div className="neo-border bg-neo-black p-3">
                            <span className="block text-xs font-black uppercase text-neo-white">BPM</span>
                            <span className="text-lg font-black text-neo-pink">
                                {analysis_criteria.bpm}±10
                            </span>
                        </div>
                        <div className="neo-border bg-neo-black p-3">
                            <span className="block text-xs font-black uppercase text-neo-white">BRIGHTNESS</span>
                            <span className="text-lg font-black text-neo-blue">
                                {Math.round(analysis_criteria.brightness)}Hz
                            </span>
                        </div>
                        <div className="neo-border bg-neo-black p-3">
                            <span className="block text-xs font-black uppercase text-neo-white">CONFIDENCE</span>
                            <span className="text-lg font-black text-neo-white">
                                {Math.round(analysis_criteria.key_confidence * 100)}%
                            </span>
                        </div>
                    </div>
                </div>

                {/* Brutalist Results */}
                {similar_uploads.length === 0 ? (
                    <div className="neo-border neo-shadow bg-neo-pink p-8">
                        <div className="text-center">
                            <Users className="h-16 w-16 mx-auto mb-6 text-neo-white" />
                            <h3 className="text-2xl font-black uppercase tracking-wide text-neo-white mb-4">
                                NO SIMILAR TRACKS FOUND
                            </h3>
                            <p className="text-neo-white font-bold max-w-md mx-auto mb-6">
                                WE COULDN'T FIND ANY TRACKS IN YOUR LIBRARY THAT MATCH THE MUSICAL CHARACTERISTICS 
                                OF "{uploadData.title.toUpperCase()}". TRY UPLOADING MORE MUSIC TO BUILD A LARGER COLLECTION FOR COMPARISON.
                            </p>
                            <Link href={route('uploads.create')}>
                                <Button variant="neutral" className="font-black uppercase neo-shadow">
                                    <Music className="h-4 w-4 mr-2" />
                                    UPLOAD MORE MUSIC
                                </Button>
                            </Link>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Results Header */}
                        <div className="neo-border neo-shadow bg-neo-black p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="text-xl font-black uppercase tracking-wider text-neo-white">
                                        SIMILAR TRACKS
                                    </h2>
                                    <p className="font-bold text-neo-green">
                                        {similar_uploads.length} MATCHES FOUND • SORTED BY BPM SIMILARITY
                                    </p>
                                </div>
                                <Users className="h-8 w-8 text-neo-white" />
                            </div>
                        </div>

                        {/* Results Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {similar_uploads.map((similarUpload, index) => (
                                <BrutalistSimilarTrackCard 
                                    key={similarUpload.id} 
                                    upload={similarUpload} 
                                    index={index} 
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Brutalist Actions */}
                <div className="neo-border neo-shadow bg-neo-green p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-black uppercase tracking-wide text-neo-black text-lg">DISCOVER MORE</h4>
                            <p className="font-bold text-neo-black text-sm">
                                UPLOAD MORE TRACKS TO IMPROVE SIMILARITY MATCHING
                            </p>
                        </div>
                        <div className="flex gap-3">
                            <Link href={route('uploads.create')}>
                                <Button variant="neutral" className="font-black uppercase neo-shadow">
                                    <Music className="h-4 w-4 mr-2" />
                                    UPLOAD MUSIC
                                </Button>
                            </Link>
                            <Link href={route('uploads.index')}>
                                <Button variant="neutral" className="font-black uppercase neo-shadow">
                                    BROWSE LIBRARY
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}