import { DeleteConfirmationDialog } from '@/components/delete-confirmation-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { router } from '@inertiajs/react';
import { Calendar, Clock, Download, MoreVertical, Music, Pencil, Trash2, User, Volume2 } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

export interface Upload {
    id: number;
    title: string;
    description: string | null;
    filename: string;
    mime_type: string;
    size: number;
    status: string;
    stream_url: string | null;
    created_at: string;
    updated_at: string;
    user: {
        id: number;
        name: string;
    };
    artist?: string;
    duration?: number;
    genre?: string;
    bitrate?: number;
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

// Helper function to format date
const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
};

// Helper function to get audio format from mime type
const getAudioFormat = (mimeType: string): string => {
    const formats: { [key: string]: string } = {
        'audio/mpeg': 'MP3',
        'audio/wav': 'WAV',
        'audio/flac': 'FLAC',
        'audio/aac': 'AAC',
        'audio/ogg': 'OGG',
        'audio/m4a': 'M4A',
        'audio/wma': 'WMA',
    };
    return formats[mimeType] || 'AUDIO';
};

// Helper function to get status color
const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
        case 'completed':
        case 'success':
        case 'ready':
            return 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 dark:hover:bg-green-900/40';
        case 'processing':
        case 'pending':
            return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300 dark:hover:bg-yellow-900/40';
        case 'failed':
        case 'error':
            return 'bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/40';
        default:
            return 'bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700';
    }
};

// Individual music upload card component
export const MusicCard = ({
    upload,
    isLast,
    lastElementRef,
}: {
    upload: Upload;
    isLast: boolean;
    lastElementRef?: (node: HTMLDivElement | null) => void;
}) => {
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDelete = () => {
        setIsDeleting(true);

        router.delete(route('uploads.destroy', upload.id), {
            onSuccess: () => {
                setIsDeleteDialogOpen(false);
                setIsDeleting(false);
                // Toast will be handled by the flash message in the Index component
            },
            onError: () => {
                setIsDeleteDialogOpen(false);
                setIsDeleting(false);
                toast.error('Failed to delete the upload. Please try again.');
            },
            // Important: preserve the flash message state but don't preserve scroll position
            preserveScroll: false,
            preserveState: false,
        });
    };

    return (
        <Card
            ref={isLast ? lastElementRef : null}
            className="group cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
            onClick={(e) => {
                // Prevent navigation during delete actions
                if (isDeleteDialogOpen || isDeleting) {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }

                router.visit(route('uploads.show', upload.id));
            }}
        >
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs dark:border-gray-600 dark:text-gray-300">
                            {getAudioFormat(upload.mime_type)}
                        </Badge>
                        <Badge className={getStatusColor(upload.status)}>{upload.status.charAt(0).toUpperCase() + upload.status.slice(1)}</Badge>
                    </div>
                    <div className="opacity-0 transition-opacity group-hover:opacity-100">
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" onClick={(e) => e.stopPropagation()}>
                                    <MoreVertical className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                                <DropdownMenuItem
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        router.visit(route('uploads.edit', upload.id));
                                    }}
                                >
                                    <Pencil className="mr-2 h-4 w-4" />
                                    Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                    <Download className="mr-2 h-4 w-4" />
                                    Download
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    className="text-destructive"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setIsDeleteDialogOpen(true);
                                    }}
                                >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Delete
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </CardHeader>

            <DeleteConfirmationDialog
                isOpen={isDeleteDialogOpen}
                onClose={() => setIsDeleteDialogOpen(false)}
                onConfirm={handleDelete}
                title="Delete Audio File"
                description={`Are you sure you want to delete "${upload.title}"? This action cannot be undone and all data will be permanently removed.`}
                deleteButtonText="Delete"
                cancelButtonText="Cancel"
                isLoading={isDeleting}
            />

            <CardContent className="space-y-4">
                {/* Music Visualization */}
                <div className="flex aspect-square items-center justify-center overflow-hidden rounded-lg bg-gradient-to-br from-white to-blue-100 dark:from-slate-800 dark:to-blue-950">
                    <div className="flex flex-col items-center justify-center">
                        <Music className="mb-2 h-12 w-12 text-blue-500 dark:text-blue-400" />
                        <div className="flex items-center space-x-1">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div
                                    key={i}
                                    className={`w-1 animate-pulse rounded-full bg-blue-400/70 dark:bg-blue-500/70`}
                                    style={{
                                        height: `${15 + Math.floor(Math.random() * 20)}px`,
                                        animationDelay: `${i * 0.1}s`,
                                    }}
                                ></div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Music Info */}
                <div className="space-y-2">
                    <h3 className="line-clamp-1 text-lg leading-tight font-semibold dark:text-white">{upload.title}</h3>
                    {upload.artist && <p className="line-clamp-1 text-sm font-medium text-gray-600 dark:text-gray-300">by {upload.artist}</p>}
                    {upload.description && <p className="line-clamp-2 text-xs text-gray-500 dark:text-gray-400">{upload.description}</p>}
                </div>

                {/* Technical Details */}
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 dark:text-gray-400">
                    {upload.duration && (
                        <div className="flex items-center space-x-1">
                            <Clock className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                            <span>{formatDuration(upload.duration)}</span>
                        </div>
                    )}
                    <div className="flex items-center space-x-1">
                        <Volume2 className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                        <span>{formatFileSize(upload.size)}</span>
                    </div>
                    {upload.bitrate && (
                        <div className="flex items-center space-x-1">
                            <span className="text-xs text-gray-400 dark:text-gray-500">♪</span>
                            <span>{upload.bitrate} kbps</span>
                        </div>
                    )}
                    {upload.genre && (
                        <div className="flex items-center space-x-1">
                            <span className="text-xs text-gray-400 dark:text-gray-500">#</span>
                            <span className="truncate">{upload.genre}</span>
                        </div>
                    )}
                </div>
            </CardContent>

            <CardFooter className="pt-0">
                <div className="flex w-full items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex items-center space-x-1">
                        <User className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                        <span className="truncate">{upload.user.name}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                        <Calendar className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                        <span>{formatDate(upload.created_at)}</span>
                    </div>
                </div>
            </CardFooter>
        </Card>
    );
};
