import { MusicCard } from '@/components/music-library-card';
import { StatCard } from '@/components/stat-card';
import { Button } from '@/components/ui/button';
import { UploadSelectionDialog } from '@/components/upload-selection-dialog';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem, type SharedData, type Upload } from '@/types';
import { Head, Link, router, usePage } from '@inertiajs/react';
import { BarChart3, CheckCircle, Music, Scissors, Upload as UploadIcon } from 'lucide-react';

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Dashboard',
        href: '/dashboard',
    },
];

interface DashboardProps {
    recentUploads: {
        data: Upload[];
    };
}

export default function Dashboard({ recentUploads }: DashboardProps) {
    const { auth } = usePage<SharedData>().props;
    const firstName = auth.user.name.split(' ')[0];

    const handleStemSelection = (upload: Upload) => {
        router.post(
            `/uploads/${upload.id}/stems`,
            {},
            {
                onSuccess: () => {
                    router.visit(`/uploads/${upload.id}/stems?from=dashboard`);
                },
            },
        );
    };

    const handleAnalysisSelection = (upload: Upload) => {
        router.post(
            `/uploads/${upload.id}/analysis`,
            {},
            {
                onSuccess: () => {
                    router.visit(`/uploads/${upload.id}/analysis?from=dashboard`);
                },
            },
        );
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Dashboard" />
            <div className="flex h-full flex-1 flex-col gap-8 overflow-x-auto p-6">
                {/* Hero greeting */}
                <section className="mb-2">
                    <h1 className="font-serif text-3xl text-foreground mb-1">
                        Good morning, {firstName}
                    </h1>
                    <p className="text-sm text-muted-foreground">
                        {recentUploads.data.length} {recentUploads.data.length === 1 ? 'track' : 'tracks'} in your library
                    </p>
                </section>

                {/* Stats grid */}
                <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <StatCard
                        title="Total uploads"
                        value={recentUploads.data.length}
                        icon={<UploadIcon className="h-5 w-5" />}
                    />
                    <StatCard
                        title="Processed"
                        value={recentUploads.data.filter((u) => u.status === 'ready').length}
                        icon={<CheckCircle className="h-5 w-5" />}
                    />
                    <StatCard
                        title="Analyzing"
                        value={recentUploads.data.filter((u) => u.status === 'processing').length}
                        icon={<BarChart3 className="h-5 w-5" />}
                    />
                </section>

                {/* Action buttons */}
                <div className="grid gap-4 md:grid-cols-3">
                    <Button asChild variant="secondary" className="h-12 gap-2">
                        <Link href="/uploads/create?from=dashboard">
                            <Music className="size-4" />
                            Upload a track
                        </Link>
                    </Button>

                    <UploadSelectionDialog
                        title="Create stems"
                        description="Select an upload to separate into individual stems (vocals, drums, bass, etc.)"
                        actionLabel="Create stems"
                        actionType="stems"
                        onUploadSelect={handleStemSelection}
                    >
                        <Button variant="secondary" className="h-12 gap-2">
                            <Scissors className="size-4" />
                            Create stems
                        </Button>
                    </UploadSelectionDialog>

                    <UploadSelectionDialog
                        title="Song analysis"
                        description="Select an upload to analyze for musical properties like key, BPM, and more"
                        actionLabel="Analyze song"
                        actionType="analysis"
                        onUploadSelect={handleAnalysisSelection}
                    >
                        <Button variant="secondary" className="h-12 gap-2">
                            <BarChart3 className="size-4" />
                            Song analysis
                        </Button>
                    </UploadSelectionDialog>
                </div>

                {/* Recent uploads */}
                <section>
                    <h2 className="font-sans text-lg font-semibold text-foreground mb-4">Recent uploads</h2>

                    {recentUploads.data.length === 0 ? (
                        <div className="studio-card p-12 text-center">
                            <div className="w-14 h-14 rounded-full bg-[--amber]/10 flex items-center justify-center mx-auto mb-4">
                                <Music className="h-6 w-6 text-[--amber]" />
                            </div>
                            <h3 className="font-serif text-xl text-foreground mb-2">Your library is empty</h3>
                            <p className="text-sm text-muted-foreground mb-6">Upload your first track to get started.</p>
                            <Button asChild>
                                <Link href="/uploads/create">Upload a track</Link>
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {recentUploads.data.map((upload) => (
                                <MusicCard key={upload.id} upload={upload} isLast={false} />
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </AppLayout>
    );
}
