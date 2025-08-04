import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { DeleteUploadDialog } from '@/components/delete-upload-dialog';
import { formatFileSize, formatDuration, formatDate } from '@/lib/formatters';
import { getAudioFormat, getStatusColor } from '@/lib/upload-helpers';
import { Upload } from '@/types';
import { Link, router } from '@inertiajs/react';
import { Calendar, Clock, Download, MoreVertical, Music, Pencil, Trash2, User, Volume2 } from 'lucide-react';
import { useState } from 'react';


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

    const handleCardClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        router.visit(route('uploads.show', upload.id));
    };

    return (
        <>
            <Card
                ref={isLast ? lastElementRef : null}
                className="group cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-md dark:hover:shadow-slate-700/20 dark:border-slate-800"
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
                                <Button variant="ghost" size="icon" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                                    <MoreVertical className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="w-56" align="end" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
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
                                    onClick={(e: React.MouseEvent) => {
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
                <div className="flex aspect-square items-center justify-center overflow-hidden rounded-lg bg-gradient-to-br from-white to-blue-100 dark:from-slate-800/80 dark:to-blue-950/90 border dark:border-slate-700/50">
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
        <DeleteUploadDialog
            upload={upload}
            isOpen={deleteDialogOpen}
            onOpenChange={setDeleteDialogOpen}
        />
        </>
    );
};
