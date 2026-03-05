import { DeleteUploadDialog } from '@/components/delete-upload-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { formatDate, formatDuration, formatFileSize } from '@/lib/formatters';
import { getAudioFormat } from '@/lib/upload-helpers';
import { cn } from '@/lib/utils';
import { Upload } from '@/types';
import { Link, router } from '@inertiajs/react';
import { BarChart3, Calendar, Clock, Download, Gauge, MoreVertical, Pencil, Scissors, Trash2, Volume2 } from 'lucide-react';
import { useState } from 'react';

const statusVariantMap: Record<string, 'success' | 'processing' | 'destructive' | 'warning' | 'secondary'> = {
    ready: 'success',
    processing: 'processing',
    failed: 'destructive',
    pending: 'warning',
};

// Deterministic pseudo-random waveform based on upload id
function getBarHeight(uploadId: number, barIndex: number): number {
    const seed = (uploadId * 37 + barIndex * 13) % 100;
    return 8 + Math.abs(Math.sin(seed * 0.4)) * 36;
}

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
            <div
                ref={isLast ? lastElementRef : null}
                className="studio-card cursor-pointer group overflow-hidden p-0"
                onClick={handleCardClick}
            >
                {/* Waveform area */}
                <div className="relative h-24 bg-[--surface-2] overflow-hidden flex items-center px-4">
                    <div className="flex items-end gap-0.5 h-full py-4 flex-1">
                        {Array.from({ length: 48 }).map((_, i) => (
                            <div
                                key={i}
                                className="flex-1 rounded-full bg-[--amber]/40 group-hover:bg-[--amber]/60 transition-colors duration-200"
                                style={{ height: `${getBarHeight(upload.id, i)}px` }}
                            />
                        ))}
                    </div>
                    {/* Hover overlay */}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-2">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); router.visit(route('uploads.analysis.show', { upload: upload.id })); }}
                        >
                            <BarChart3 className="h-3.5 w-3.5" />
                            Analysis
                        </Button>
                    </div>
                </div>

                {/* Card body */}
                <div className="p-4 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                            <h3 className="font-medium text-sm text-foreground truncate">{upload.title}</h3>
                            {upload.artist && <p className="text-xs text-muted-foreground truncate">by {upload.artist}</p>}
                        </div>
                        <DropdownMenu modal={false}>
                            <DropdownMenuTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                    onClick={(e: React.MouseEvent) => e.stopPropagation()}
                                >
                                    <MoreVertical className="h-3.5 w-3.5" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="w-52" align="end" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                                <DropdownMenuItem asChild>
                                    <Link href={route('uploads.analysis.show', { upload: upload.id })} className="flex items-center">
                                        <BarChart3 className="mr-2 h-4 w-4" />
                                        Audio analysis
                                        {upload.has_analysis && <Badge variant="success" className="ml-auto text-xs">Done</Badge>}
                                        {upload.is_analysis_in_progress && <Badge variant="processing" className="ml-auto text-xs">Processing</Badge>}
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild>
                                    <Link href={route('uploads.stems.show', { upload: upload.id })} className="flex items-center">
                                        <Scissors className="mr-2 h-4 w-4" />
                                        Stem separation
                                        {upload.has_stems && <Badge variant="success" className="ml-auto text-xs">Done</Badge>}
                                        {upload.is_stem_separation_in_progress && <Badge variant="processing" className="ml-auto text-xs">Processing</Badge>}
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild>
                                    <Link href={route('uploads.tempo.show', { upload: upload.id })} className="flex items-center">
                                        <Gauge className="mr-2 h-4 w-4" />
                                        Tempo effects
                                        {upload.has_tempos && <Badge variant="success" className="ml-auto text-xs">Done</Badge>}
                                        {upload.is_tempo_processing_in_progress && <Badge variant="processing" className="ml-auto text-xs">Processing</Badge>}
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild>
                                    <Link href={route('uploads.edit', { upload: upload.id })} className="flex items-center">
                                        <Pencil className="mr-2 h-4 w-4" />
                                        Edit
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild>
                                    <Link href={route('uploads.show', { upload: upload.id })} className="flex items-center">
                                        <Download className="mr-2 h-4 w-4" />
                                        View details
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    className="text-destructive focus:text-destructive"
                                    onClick={(e: React.MouseEvent) => { e.stopPropagation(); setDeleteDialogOpen(true); }}
                                >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Delete
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>

                    <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 flex-wrap">
                            <Badge variant={statusVariantMap[upload.status] ?? 'secondary'}>
                                {upload.status.charAt(0).toUpperCase() + upload.status.slice(1)}
                            </Badge>
                            <Badge variant="outline" className="text-xs">{getAudioFormat(upload.mime_type)}</Badge>
                        </div>
                        <div className={cn("flex items-center gap-3 text-xs text-muted-foreground font-mono")}>
                            {upload.duration && (
                                <span className="flex items-center gap-1">
                                    <Clock className="h-3 w-3" />
                                    {formatDuration(upload.duration)}
                                </span>
                            )}
                            <span className="flex items-center gap-1">
                                <Volume2 className="h-3 w-3" />
                                {formatFileSize(upload.size)}
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                            {upload.has_analysis && <Badge variant="success" className="text-xs"><BarChart3 className="h-2.5 w-2.5" />Analysis</Badge>}
                            {upload.has_stems && <Badge variant="success" className="text-xs"><Scissors className="h-2.5 w-2.5" />Stems</Badge>}
                            {upload.has_tempos && <Badge variant="success" className="text-xs"><Gauge className="h-2.5 w-2.5" />Tempo</Badge>}
                        </div>
                        <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(upload.created_at)}
                        </span>
                    </div>
                </div>
            </div>

            <DeleteUploadDialog upload={upload} isOpen={deleteDialogOpen} onOpenChange={setDeleteDialogOpen} />
        </>
    );
};
