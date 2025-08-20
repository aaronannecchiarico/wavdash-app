import { UploadSelectionDialog } from '@/components/upload-selection-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import { formatDistance } from 'date-fns';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, Link, router } from '@inertiajs/react';
import { Music, Scissors, BarChart3, Clock, Gauge } from 'lucide-react';

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
            <div className="flex h-full flex-1 flex-col gap-8 overflow-x-auto rounded-xl p-6">
                {/* Main Action Buttons */}
                <div className="grid gap-6 md:grid-cols-3">
                    <Button asChild className="h-16 flex-col gap-1.5">
                        <Link href="/uploads/create?from=dashboard">
                            <Music className="size-5" />
                            <span className="text-sm font-medium">Upload a Song</span>
                        </Link>
                    </Button>
                    
                    <UploadSelectionDialog
                        title="Create Stems"
                        description="Select an upload to separate into individual stems (vocals, drums, bass, etc.)"
                        actionLabel="Create Stems"
                        actionType="stems"
                        onUploadSelect={handleStemSelection}
                    >
                        <Button className="h-16 flex-col gap-1.5" variant="outline">
                            <Scissors className="size-5" />
                            <span className="text-sm font-medium">Create Stems</span>
                        </Button>
                    </UploadSelectionDialog>
                    
                    <UploadSelectionDialog
                        title="Song Analysis"
                        description="Select an upload to analyze for musical properties like key, BPM, and more"
                        actionLabel="Analyze Song"
                        actionType="analysis"
                        onUploadSelect={handleAnalysisSelection}
                    >
                        <Button className="h-16 flex-col gap-1.5" variant="outline">
                            <BarChart3 className="size-5" />
                            <span className="text-sm font-medium">Song Analysis</span>
                        </Button>
                    </UploadSelectionDialog>
                </div>

                {/* Recent Uploads */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold">Recent Uploads</h2>
                        <Button asChild variant="ghost" size="sm">
                            <Link href="/uploads">View All</Link>
                        </Button>
                    </div>
                    
                    {recentUploads.data.length === 0 ? (
                        <Card>
                            <CardContent className="flex flex-col items-center justify-center py-12">
                                <Music className="size-12 text-muted-foreground mb-4" />
                                <h3 className="text-lg font-medium mb-2">No uploads yet</h3>
                                <p className="text-muted-foreground text-center mb-4">
                                    Upload your first song to get started with Beat Forge.
                                </p>
                                <Button asChild>
                                    <Link href="/uploads/create">Upload a Song</Link>
                                </Button>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="space-y-4">
                            {recentUploads.data.map((upload) => (
                                <Card 
                                    key={upload.id} 
                                    className="cursor-pointer hover:bg-accent/50 transition-colors"
                                    onClick={() => router.visit(`/uploads/${upload.id}?from=dashboard`)}
                                >
                                    <CardContent className="p-6">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h3 className="font-medium truncate">{upload.title}</h3>
                                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                        upload.status === 'ready' 
                                                            ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                                            : upload.status === 'processing'
                                                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                                                            : 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                                                    }`}>
                                                        {upload.status}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-muted-foreground truncate mb-1">
                                                    {upload.filename}
                                                </p>
                                                {upload.description && (
                                                    <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                                                        {upload.description}
                                                    </p>
                                                )}
                                                
                                                {/* Processing badges */}
                                                <div className="flex flex-wrap gap-1 mt-2">
                                                    {upload.has_analysis && (
                                                        <Badge variant="secondary" className="text-xs">
                                                            <BarChart3 className="mr-1 h-3 w-3" />
                                                            Analysis
                                                        </Badge>
                                                    )}
                                                    {upload.has_stems && (
                                                        <Badge variant="secondary" className="text-xs">
                                                            <Scissors className="mr-1 h-3 w-3" />
                                                            Stems
                                                        </Badge>
                                                    )}
                                                    {upload.has_tempos && (
                                                        <Badge variant="secondary" className="text-xs">
                                                            <Gauge className="mr-1 h-3 w-3" />
                                                            Tempo Effects
                                                        </Badge>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end text-xs text-muted-foreground ml-4">
                                                <div className="flex items-center gap-1">
                                                    <Clock className="size-3" />
                                                    {formatDistance(new Date(upload.created_at), new Date(), { addSuffix: true })}
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </AppLayout>
    );
}
