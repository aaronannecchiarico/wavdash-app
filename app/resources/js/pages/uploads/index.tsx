import { MusicCard } from '@/components/music-library-card';
import { MusicLibraryControls } from '@/components/music-library-controls';
import { Button } from '@/components/ui/button';
import AppLayout from '@/layouts/app-layout';
import { formatDuration, formatFileSize } from '@/lib/formatters';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, usePage } from '@inertiajs/react';
import { Music, PlusIcon } from 'lucide-react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface Props {
    uploads: {
        data: Upload[];
        links: {
            first: string | null;
            last: string | null;
            prev: string | null;
            next: string | null;
        };
    };
    filters: {
        status?: string;
        type?: string;
        sort?: string;
        direction?: string;
        analysis_status?: string;
        stems_status?: string;
        tempo_status?: string;
    };
    filterOptions: {
        statuses: string[];
        types: string[];
        processingStatuses: Record<string, string>;
    };
}

export default function Index({ uploads, filters, filterOptions }: Props) {
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

    const estimatedTotalDuration = uploads.data.reduce((acc, upload) => acc + (upload.duration || Math.floor(upload.size / 10000)), 0);
    const totalSize = uploads.data.reduce((acc, upload) => acc + upload.size, 0);

    const breadcrumbs: BreadcrumbItem[] = [
        {
            title: 'Music Library',
            href: route('uploads.index'),
            description: `${uploads.data.length} ${uploads.data.length === 1 ? 'track' : 'tracks'} • ${formatDuration(estimatedTotalDuration)} total • ${formatFileSize(totalSize)}`,
        },
    ];

    const hasFilters = Object.values(filters).some(Boolean);

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Music Library" />
            <div className="p-4 sm:p-6 lg:p-8">
                <div className="mb-6 flex items-center justify-between">
                    {uploads.data.length > 0 && <MusicLibraryControls filters={filters} filterOptions={filterOptions} />}
                    <Link href={route('uploads.create')} className={uploads.data.length === 0 ? 'ml-auto' : ''}>
                        <Button>
                            <PlusIcon className="mr-2 h-4 w-4" />
                            Upload a track
                        </Button>
                    </Link>
                </div>
                <div className="flex h-full flex-1 flex-col gap-4 pb-8">
                    {uploads.data.length === 0 ? (
                        <div className="studio-card p-12 text-center">
                            <div className="w-14 h-14 rounded-full bg-[--amber]/10 flex items-center justify-center mx-auto mb-4">
                                <Music className="h-6 w-6 text-[--amber]" />
                            </div>
                            <h3 className="font-serif text-xl text-foreground mb-2">
                                {hasFilters ? 'No results found' : 'Your library is empty'}
                            </h3>
                            <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
                                {hasFilters
                                    ? 'Try adjusting your filters to find what you\'re looking for.'
                                    : 'Upload your first track to get started with stem separation, BPM analysis, and more.'}
                            </p>
                            {!hasFilters && (
                                <Button asChild>
                                    <Link href={route('uploads.create')}>
                                        <PlusIcon className="mr-2 h-4 w-4" />
                                        Upload your first track
                                    </Link>
                                </Button>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Grid - Bigger cards with better spacing */}
                            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                                {uploads.data.map((upload, index) => (
                                    <MusicCard key={upload.id} upload={upload} isLast={index === uploads.data.length - 1} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </AppLayout>
    );
}
