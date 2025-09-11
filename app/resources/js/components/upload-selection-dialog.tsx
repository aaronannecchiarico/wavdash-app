import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Upload } from '@/types';
import { Link } from '@inertiajs/react';
import { CheckCircle, PlusIcon, SearchIcon } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface UploadSelectionDialogProps {
    title: string;
    description: string;
    actionLabel: string;
    actionType: 'stems' | 'analysis';
    onUploadSelect: (upload: Upload) => void;
    children: React.ReactNode;
}

export function UploadSelectionDialog({ title, description, actionLabel, actionType, onUploadSelect, children }: UploadSelectionDialogProps) {
    const [open, setOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
    const [uploads, setUploads] = useState<Upload[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchUploads = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch(`/api/uploads?search=${encodeURIComponent(debouncedSearchQuery)}&limit=20`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
                },
                credentials: 'same-origin',
            });
            if (response.ok) {
                const data = await response.json();
                setUploads(data.uploads || []);
            } else {
                console.error('Failed to fetch uploads:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('Failed to fetch uploads:', error);
        } finally {
            setLoading(false);
        }
    }, [debouncedSearchQuery]);

    // Debounce search query
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearchQuery(searchQuery);
        }, 300);

        return () => clearTimeout(timer);
    }, [searchQuery]);

    useEffect(() => {
        if (open) {
            fetchUploads();
        }
    }, [open, fetchUploads]);

    const handleUploadSelect = (upload: Upload) => {
        onUploadSelect(upload);
        setOpen(false);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>{children}</DialogTrigger>
            <DialogContent className="flex h-[80vh] max-w-2xl flex-col">
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                    <DialogDescription>{description}</DialogDescription>
                </DialogHeader>

                <div className="flex flex-1 flex-col space-y-6 overflow-hidden">
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <SearchIcon className="absolute top-1/2 left-3 size-4 -translate-y-1/2 transform text-muted-foreground" />
                            <Input
                                placeholder="Search uploads..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                            />
                        </div>
                        <Button asChild variant="neutral">
                            <Link href="/uploads/create">
                                <PlusIcon />
                                New Upload
                            </Link>
                        </Button>
                    </div>

                    <div className="flex-1 space-y-3 overflow-y-auto">
                        {loading ? (
                            <div className="space-y-2">
                                {[...Array(5)].map((_, i) => (
                                    <Card key={i} className="animate-pulse">
                                        <CardContent className="p-5">
                                            <div className="mb-2 h-4 w-3/4 rounded bg-muted"></div>
                                            <div className="h-3 w-1/2 rounded bg-muted"></div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        ) : uploads.length === 0 ? (
                            <div className="py-8 text-center text-muted-foreground">
                                {searchQuery ? 'No uploads found matching your search.' : 'No uploads available.'}
                            </div>
                        ) : (
                            uploads.map((upload) => {
                                const isCompleted = actionType === 'stems' ? upload.has_stems : upload.has_analysis;

                                return (
                                    <Card
                                        key={upload.id}
                                        className="cursor-pointer transition-colors hover:bg-accent/50"
                                        onClick={() => handleUploadSelect(upload)}
                                    >
                                        <CardContent className="p-5">
                                            <div className="flex items-start justify-between">
                                                <div className="min-w-0 flex-1">
                                                    <div className="mb-1 flex items-center gap-2">
                                                        <h4 className="truncate font-medium">{upload.title}</h4>
                                                        {isCompleted && (
                                                            <div className="flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800 dark:bg-green-900/20 dark:text-green-400">
                                                                <CheckCircle className="size-3" />
                                                                Done
                                                            </div>
                                                        )}
                                                    </div>
                                                    <p className="truncate text-sm text-muted-foreground">{upload.filename}</p>
                                                    {upload.description && (
                                                        <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{upload.description}</p>
                                                    )}
                                                </div>
                                                <div className="ml-4 flex flex-col items-end text-xs text-muted-foreground">
                                                    <span
                                                        className={`rounded-full px-2 py-1 text-xs font-medium ${
                                                            upload.status === 'ready'
                                                                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                                                : upload.status === 'processing'
                                                                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                                                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                                                        }`}
                                                    >
                                                        {upload.status}
                                                    </span>
                                                </div>
                                            </div>
                                            <Button
                                                size="sm"
                                                className="mt-3 w-full"
                                                variant={isCompleted ? 'neutral' : 'default'}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleUploadSelect(upload);
                                                }}
                                            >
                                                {isCompleted ? `Re-${actionLabel}` : actionLabel}
                                            </Button>
                                        </CardContent>
                                    </Card>
                                );
                            })
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
