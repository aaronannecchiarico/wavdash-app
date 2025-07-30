import { MusicCard, type Upload } from '@/components/music-library-card';
import { Button } from '@/components/ui/button';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
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
}

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Helper function to format duration
const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export default function Index({ uploads }: Props) {
    // Get the page props with proper type
    const { props } = usePage();

    // Use a more specific type for accessing flash messages
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

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Music Library" />
            <Link href={route('uploads.create')}>
                <Button
                    className="fixed right-6 bottom-6 z-50 h-14 w-14 rounded-full bg-blue-600 p-0 shadow-lg transition-all duration-200 hover:scale-105 hover:bg-blue-700 hover:shadow-xl dark:bg-blue-700 dark:hover:bg-blue-600"
                    size="lg"
                >
                    <PlusIcon className="h-6 w-6" />
                </Button>
            </Link>
            <div className="flex h-full flex-1 flex-col gap-4 overflow-x-auto rounded-xl p-4">
                {uploads.data.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-white to-blue-100 dark:from-slate-800/50 dark:to-blue-900/30">
                            <Music className="h-8 w-8 text-blue-500 dark:text-blue-400" />
                        </div>
                        <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">No music files found</h3>
                        <p className="max-w-sm text-gray-500 dark:text-gray-400">
                            {"You haven't uploaded any audio files yet. Upload some tracks to get started."}
                        </p>
                        <div className="mt-6">
                            <Link href={route('uploads.create')}>
                                <Button className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600">
                                    <PlusIcon className="mr-2 h-5 w-5" />
                                    Upload Your First Beat
                                </Button>
                            </Link>
                        </div>
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
        </AppLayout>
    );
}
