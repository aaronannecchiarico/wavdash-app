import { MusicCard } from '@/components/music-library-card';
import { MusicLibraryControls } from '@/components/music-library-controls';
import { Button } from '@/components/ui/button';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, usePage } from '@inertiajs/react';
import { Music, PlusIcon } from 'lucide-react';
import { useEffect } from 'react';
import { toast } from 'sonner';
import { formatFileSize, formatDuration } from '@/lib/formatters';

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
                <div className="mb-4 flex items-center justify-between">
                    <MusicLibraryControls filters={filters} filterOptions={filterOptions} />
                    <Link href={route('uploads.create')}>
                        <Button className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600">
                            <PlusIcon className="mr-2 h-4 w-4" />
                            Create Upload
                        </Button>
                    </Link>
                </div>
                <div className="flex h-full flex-1 flex-col gap-4 overflow-x-auto rounded-xl">
                    {uploads.data.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-white to-blue-100 dark:from-slate-800/50 dark:to-blue-900/30">
                                <Music className="h-8 w-8 text-blue-500 dark:text-blue-400" />
                            </div>
                            <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">No music files found</h3>
                            <p className="max-w-sm text-gray-500 dark:text-gray-400">
                                {hasFilters
                                    ? 'Your search returned no results. Try adjusting your filters.'
                                    : "You haven't uploaded any audio files yet. Upload some tracks to get started."}
                            </p>
                            {!hasFilters && (
                                <div className="mt-6">
                                    <Link href={route('uploads.create')}>
                                        <Button className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600">
                                            <PlusIcon className="mr-2 h-5 w-5" />
                                            Upload Your First Beat
                                        </Button>
                                    </Link>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Grid */}
                            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
