import { BrutalistDropdownMenu } from '@/components/brutalist-dropdown-menu';
import { formatDate, formatDuration, formatFileSize, getAudioFormat } from '@/lib/formatters';
import { type Upload } from '@/types';
import { router } from '@inertiajs/react';

interface BrutalistMusicCardProps {
    upload: Upload;
    isLast?: boolean;
    lastElementRef?: (node: HTMLDivElement | null) => void;
}

export function BrutalistMusicCard({ upload, isLast, lastElementRef }: BrutalistMusicCardProps) {
    const statusColors = {
        ready: 'bg-chart-1', // neo-green
        processing: 'bg-chart-3', // neo-yellow
        failed: 'bg-red-500',
        pending: 'bg-chart-4', // neo-blue
    };

    return (
        <div
            ref={isLast ? lastElementRef : null}
            className="cursor-pointer border-2 border-border bg-background shadow-shadow transition-all hover:translate-x-boxShadowX hover:translate-y-boxShadowY hover:shadow-none"
            onClick={() => router.visit(route('uploads.show', upload.id))}
        >
            {/* Status Header */}
            <div
                className={`${statusColors[upload.status as keyof typeof statusColors]} flex items-center justify-between border-b-2 border-border p-3`}
            >
                <div className="flex items-center space-x-2">
                    <span className="font-heading text-xs font-black tracking-widest text-main-foreground uppercase">
                        {getAudioFormat(upload.mime_type)}
                    </span>
                </div>
                <div className="font-heading text-xs font-black tracking-widest text-main-foreground uppercase">{upload.status.toUpperCase()}</div>
            </div>

            {/* Waveform Visualization */}
            <div className="bg-main-foreground p-4">
                <div className="flex h-16 items-center justify-center space-x-1">
                    {[...Array(20)].map((_, i) => (
                        <div
                            key={i}
                            className="w-1 animate-pulse bg-chart-1"
                            style={{
                                height: `${20 + Math.random() * 40}px`,
                                animationDelay: `${i * 0.1}s`,
                                animationDuration: '2s',
                            }}
                        />
                    ))}
                </div>
            </div>

            {/* Track Info */}
            <div className="space-y-3 p-4">
                <div>
                    <h3 className="mb-1 font-heading text-lg font-black tracking-wide text-foreground uppercase">{upload.title}</h3>
                    {upload.artist && <p className="text-sm font-base font-bold text-foreground/70">BY {upload.artist.toUpperCase()}</p>}
                </div>

                {/* Technical Specs */}
                <div className="grid grid-cols-2 gap-2">
                    <div className="border-2 border-border bg-chart-3/20 p-2">
                        <div className="font-heading text-xs font-black text-foreground uppercase">DURATION</div>
                        <div className="font-mono font-bold text-foreground">{formatDuration(upload.duration || 0)}</div>
                    </div>
                    <div className="border-2 border-border bg-chart-2/20 p-2">
                        <div className="font-heading text-xs font-black text-foreground uppercase">SIZE</div>
                        <div className="font-mono font-bold text-foreground">{formatFileSize(upload.size)}</div>
                    </div>
                </div>

                {/* Feature Badges */}
                <div className="flex flex-wrap gap-1">
                    {upload.has_analysis && (
                        <div className="border-2 border-border bg-chart-1 px-2 py-1">
                            <span className="font-heading text-xs font-black text-main-foreground">ANALYZED</span>
                        </div>
                    )}
                    {upload.has_stems && (
                        <div className="border-2 border-border bg-chart-2 px-2 py-1">
                            <span className="font-heading text-xs font-black text-main-foreground">STEMS</span>
                        </div>
                    )}
                    {upload.has_tempos && (
                        <div className="border-2 border-border bg-chart-4 px-2 py-1">
                            <span className="font-heading text-xs font-black text-main-foreground">TEMPO FX</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Action Footer */}
            <div className="flex items-center justify-between border-t-2 border-border bg-border p-3">
                <div className="font-mono text-xs text-foreground">{formatDate(upload.created_at).toUpperCase()}</div>
                <BrutalistDropdownMenu upload={upload} />
            </div>
        </div>
    );
}
