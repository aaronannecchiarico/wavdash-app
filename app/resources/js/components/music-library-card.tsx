import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogTitle } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Upload } from '@/types';
import { Link, router, useForm } from '@inertiajs/react';
import { Calendar, Clock, Download, MoreVertical, Music, Pencil, Trash2, User, Volume2 } from 'lucide-react';
import { useState, FormEventHandler } from 'react';

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
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const {
        delete: destroy,
        processing,
        reset,
        clearErrors,
    } = useForm();

    const closeDeleteModal = () => {
        clearErrors();
        reset();
        setDeleteDialogOpen(false);
    };

    const deleteUpload: FormEventHandler = (e) => {
        e.preventDefault();
        destroy(route('uploads.destroy', upload.id), {
            preserveScroll: true,
            onSuccess: () => closeDeleteModal(),
        });
    };

    const handleCardClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        router.visit(route('uploads.show', upload.id));
    };

    return (
        <>
            <Card
                ref={isLast ? lastElementRef : null}
                className="group cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
                onClick={handleCardClick}
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
                        <DropdownMenu modal={false}>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" onClick={(e) => e.stopPropagation()}>
                                    <MoreVertical className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="w-56" align="end" onClick={(e) => e.stopPropagation()}>
                                <DropdownMenuItem>
                                    <Link href={route('uploads.edit', upload.id)} className="flex w-full items-center">
                                        <Pencil className="mr-2 h-4 w-4" />
                                        Edit
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                    <Link href={route('uploads.index', upload.id)} className="flex w-full items-center">
                                        <Download className="mr-2 h-4 w-4" />
                                        Download
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    className="text-red-600 focus:bg-red-100 focus:text-red-700 dark:text-red-500 dark:focus:bg-red-950/50 dark:focus:text-red-400"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setDeleteDialogOpen(true);
                                    }}
                                >
                                    <div className="flex items-center">
                                        <Trash2 className="mr-2 h-4 w-4" />
                                        Delete
                                    </div>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </CardHeader>

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

        {/* Delete Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <DialogContent
                onClick={(e) => {
                    e.stopPropagation();
                }}
            >
                <DialogTitle>Are you sure you want to delete this upload?</DialogTitle>
                <DialogDescription>
                    Once this upload is deleted, it will be permanently gone. This action cannot be undone.
                </DialogDescription>
                <form onSubmit={deleteUpload} className="pt-4">
                    <DialogFooter className="gap-2">
                        <DialogClose asChild>
                            <Button type="button" variant="secondary" onClick={closeDeleteModal}>
                                Cancel
                            </Button>
                        </DialogClose>

                        <Button variant="destructive" disabled={processing}>
                            Delete Upload
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
        </>
    );
};
