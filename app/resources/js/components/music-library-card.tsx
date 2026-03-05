import { DeleteUploadDialog } from '@/components/delete-upload-dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/neo/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { formatDate, formatDuration, formatFileSize } from '@/lib/formatters';
import { getAudioFormat } from '@/lib/upload-helpers';
import { Upload } from '@/types';
import { Link, router } from '@inertiajs/react';
import { BarChart3, Calendar, Clock, Download, Gauge, MoreVertical, Pencil, Scissors, Trash2, User, Volume2 } from 'lucide-react';
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
        router.visit(route('uploads.show', { upload: upload.id }));
    };

    return (
        <>
            <Card
                ref={isLast ? lastElementRef : null}
                className="group neo-transition cursor-pointer hover:translate-x-boxShadowX hover:translate-y-boxShadowY hover:shadow-none"
                onClick={handleCardClick}
            >
                <CardHeader className="p-4 pb-3">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-2">
                            <Badge variant="secondary" className="text-xs font-base">
                                {getAudioFormat(upload.mime_type)}
                            </Badge>
                            <Badge variant="default">{upload.status.charAt(0).toUpperCase() + upload.status.slice(1)}</Badge>
                        </div>
                        <div className="opacity-0 transition-opacity group-hover:opacity-100">
                            <DropdownMenu modal={false}>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="secondary" size="icon" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                                        <MoreVertical className="h-4 w-4" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent className="w-56" align="end" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                                    <DropdownMenuItem>
                                        <Link href={route('uploads.analysis.show', { upload: upload.id })} className="flex w-full items-center">
                                            <BarChart3 className="mr-2 h-4 w-4" />
                                            Audio Analysis
                                            {upload.has_analysis && (
                                                <Badge variant="default" className="ml-auto text-xs">
                                                    Done
                                                </Badge>
                                            )}
                                            {upload.is_analysis_in_progress && (
                                                <Badge variant="secondary" className="ml-auto text-xs">
                                                    Processing
                                                </Badge>
                                            )}
                                        </Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem>
                                        <Link href={route('uploads.stems.show', { upload: upload.id })} className="flex w-full items-center">
                                            <Scissors className="mr-2 h-4 w-4" />
                                            Stem Separation
                                            {upload.has_stems && (
                                                <Badge variant="default" className="ml-auto text-xs">
                                                    Done
                                                </Badge>
                                            )}
                                            {upload.is_stem_separation_in_progress && (
                                                <Badge variant="secondary" className="ml-auto text-xs">
                                                    Processing
                                                </Badge>
                                            )}
                                        </Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem>
                                        <Link href={route('uploads.tempo.show', { upload: upload.id })} className="flex w-full items-center">
                                            <Gauge className="mr-2 h-4 w-4" />
                                            Tempo Effects
                                            {upload.has_tempos && (
                                                <Badge variant="default" className="ml-auto text-xs">
                                                    Done
                                                </Badge>
                                            )}
                                            {upload.is_tempo_processing_in_progress && (
                                                <Badge variant="secondary" className="ml-auto text-xs">
                                                    Processing
                                                </Badge>
                                            )}
                                        </Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem>
                                        <Link href={route('uploads.edit', { upload: upload.id })} className="flex w-full items-center">
                                            <Pencil className="mr-2 h-4 w-4" />
                                            Edit
                                        </Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem>
                                        <Link href={route('uploads.show', { upload: upload.id })} className="flex w-full items-center">
                                            <Download className="mr-2 h-4 w-4" />
                                            View Details
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

                <CardContent className="space-y-6 p-6">
                    {/* Music Visualization */}
                    <div className="flex aspect-square items-center justify-center overflow-hidden border-2 border-border bg-[var(--neo-bg-secondary)]">
                        <div className="flex flex-col items-center justify-center">
                            <div className="flex items-center space-x-1">
                                {[1, 2, 3, 4, 5].map((i) => (
                                    <div
                                        key={i}
                                        className={`w-1.5 animate-pulse`}
                                        style={{
                                            height: `${20 + Math.floor(Math.random() * 25)}px`,
                                            animationDelay: `${i * 0.1}s`,
                                            backgroundColor: 'var(--neo-white)',
                                        }}
                                    ></div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Music Info */}
                    <div className="space-y-2">
                        <h3 className="line-clamp-1 font-heading text-lg leading-tight text-foreground">{upload.title}</h3>
                        {upload.artist && <p className="line-clamp-1 text-sm font-base text-foreground">by {upload.artist}</p>}
                        {upload.description && <p className="line-clamp-2 text-xs font-base text-foreground opacity-75">{upload.description}</p>}
                    </div>

                    {/* Technical Details */}
                    <div className="grid grid-cols-2 gap-2 text-xs font-base text-foreground opacity-75">
                        {upload.duration && (
                            <div className="flex items-center space-x-1">
                                <Clock className="h-3 w-3 text-foreground" />
                                <span>{formatDuration(upload.duration)}</span>
                            </div>
                        )}
                        <div className="flex items-center space-x-1">
                            <Volume2 className="h-3 w-3 text-foreground" />
                            <span>{formatFileSize(upload.size)}</span>
                        </div>
                        {upload.bitrate && (
                            <div className="flex items-center space-x-1">
                                <span className="text-xs text-foreground">♪</span>
                                <span>{upload.bitrate} kbps</span>
                            </div>
                        )}
                        {upload.genre && (
                            <div className="flex items-center space-x-1">
                                <span className="text-xs text-foreground">#</span>
                                <span className="truncate">{upload.genre}</span>
                            </div>
                        )}
                    </div>
                </CardContent>

                <CardFooter className="p-6 pt-0">
                    <div className="flex w-full flex-col space-y-3">
                        {/* Status badges */}
                        <div className="flex flex-wrap gap-1">
                            {upload.has_analysis && (
                                <Badge variant="default" className="text-xs font-base">
                                    <BarChart3 className="mr-1 h-3 w-3" />
                                    Analysis
                                </Badge>
                            )}
                            {upload.has_stems && (
                                <Badge variant="default" className="text-xs font-base">
                                    <Scissors className="mr-1 h-3 w-3" />
                                    Stems
                                </Badge>
                            )}
                            {upload.has_tempos && (
                                <Badge variant="default" className="text-xs font-base">
                                    <Gauge className="mr-1 h-3 w-3" />
                                    Tempo Effects
                                </Badge>
                            )}
                        </div>

                        {/* User and date info */}
                        <div className="flex w-full items-center justify-between text-xs font-base text-foreground opacity-75">
                            <div className="flex items-center space-x-1">
                                <User className="h-3 w-3 text-foreground" />
                                <span className="truncate">{upload.user.name}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                                <Calendar className="h-3 w-3 text-foreground" />
                                <span>{formatDate(upload.created_at)}</span>
                            </div>
                        </div>
                    </div>
                </CardFooter>
            </Card>

            {/* Delete Dialog */}
            <DeleteUploadDialog upload={upload} isOpen={deleteDialogOpen} onOpenChange={setDeleteDialogOpen} />
        </>
    );
};
