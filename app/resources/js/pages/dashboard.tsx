import { UploadSelectionDialog } from '@/components/upload-selection-dialog';
import { BrutalistMusicCard } from '@/components/brutalist-music-card';
import { StatCard } from '@/components/stat-card';
import { Badge } from '@/components/ui/neo/badge';
import { Button } from '@/components/ui/neo/button';
import { Card, CardContent } from '@/components/ui/neo/card';
import AppLayout from '@/layouts/app-layout';
import { formatDistance } from 'date-fns';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, router } from '@inertiajs/react';
import { Music, Scissors, BarChart3, Clock, Gauge, Upload as UploadIcon, CheckCircle } from 'lucide-react';

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
    const handleStemSelection = (upload: Upload) => {
        router.post(`/uploads/${upload.id}/stems`, {}, {
            onSuccess: () => {
                router.visit(`/uploads/${upload.id}/stems?from=dashboard`);
            }
        });
    };

    const handleAnalysisSelection = (upload: Upload) => {
        router.post(`/uploads/${upload.id}/analysis`, {}, {
            onSuccess: () => {
                router.visit(`/uploads/${upload.id}/analysis?from=dashboard`);
            }
        });
    };
    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Dashboard" />
            <div className="flex h-full flex-1 flex-col gap-8 overflow-x-auto p-6">
                {/* Hero section with harsh typography */}
                <section className="border-2 border-border bg-chart-3 p-8 transition-all hover:translate-x-1 hover:translate-y-1" style={{ boxShadow: 'var(--shadow)' }}>
                    <h1 className="text-4xl font-heading font-black uppercase tracking-widest text-main-foreground mb-4">
                        YOUR BEATS
                    </h1>
                    <p className="text-lg font-base font-bold text-main-foreground">
                        {recentUploads.data.length} TRACKS READY TO DESTROY
                    </p>
                </section>

                {/* Stats grid with color blocks */}
                <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <StatCard 
                        title="TOTAL UPLOADS"
                        value={recentUploads.data.length}
                        color="bg-chart-1"
                        icon={<UploadIcon className="h-6 w-6 text-main-foreground" />}
                    />
                    <StatCard 
                        title="PROCESSED"
                        value={recentUploads.data.filter(u => u.status === 'ready').length}
                        color="bg-chart-2"
                        icon={<CheckCircle className="h-6 w-6 text-main-foreground" />}
                    />
                    <StatCard 
                        title="ANALYZING"
                        value={recentUploads.data.filter(u => u.status === 'processing').length}
                        color="bg-chart-4"
                        icon={<BarChart3 className="h-6 w-6 text-main-foreground" />}
                    />
                </section>

                {/* Main Action Buttons */}
                <div className="grid gap-6 md:grid-cols-3">
                    <Button asChild className="h-16 flex-col gap-1.5 font-heading font-black uppercase tracking-wider">
                        <Link href="/uploads/create?from=dashboard">
                            <Music className="size-5" />
                            <span className="text-sm">UPLOAD SONG</span>
                        </Link>
                    </Button>
                    
                    <UploadSelectionDialog
                        title="Create Stems"
                        description="Select an upload to separate into individual stems (vocals, drums, bass, etc.)"
                        actionLabel="Create Stems"
                        actionType="stems"
                        onUploadSelect={handleStemSelection}
                    >
                        <Button className="h-16 flex-col gap-1.5 font-heading font-black uppercase tracking-wider" variant="neutral">
                            <Scissors className="size-5" />
                            <span className="text-sm">CREATE STEMS</span>
                        </Button>
                    </UploadSelectionDialog>
                    
                    <UploadSelectionDialog
                        title="Song Analysis"
                        description="Select an upload to analyze for musical properties like key, BPM, and more"
                        actionLabel="Analyze Song"
                        actionType="analysis"
                        onUploadSelect={handleAnalysisSelection}
                    >
                        <Button className="h-16 flex-col gap-1.5 font-heading font-black uppercase tracking-wider" variant="neutral">
                            <BarChart3 className="size-5" />
                            <span className="text-sm">SONG ANALYSIS</span>
                        </Button>
                    </UploadSelectionDialog>
                </div>

                {/* Recent uploads brutalist list */}
                <section>
                    <h2 className="text-2xl font-heading font-black uppercase tracking-wide mb-6 text-foreground">
                        RECENT DROPS
                    </h2>
                    
                    {recentUploads.data.length === 0 ? (
                        <Card className="transition-all hover:translate-x-1 hover:translate-y-1">
                            <CardContent className="flex flex-col items-center justify-center py-12 bg-secondary-background">
                                <Music className="size-12 text-main-foreground mb-4" />
                                <h3 className="text-lg font-heading font-black uppercase mb-2 text-main-foreground">NO UPLOADS YET</h3>
                                <p className="text-main-foreground text-center mb-4 font-base font-bold">
                                    UPLOAD YOUR FIRST SONG TO GET STARTED WITH BEAT FORGE.
                                </p>
                                <Button asChild className="font-heading font-black uppercase tracking-wider">
                                    <Link href="/uploads/create">UPLOAD A SONG</Link>
                                </Button>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="space-y-4">
                            {recentUploads.data.map((upload) => (
                                <BrutalistMusicCard key={upload.id} upload={upload} />
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </AppLayout>
    );
}
