import { Badge } from '@/components/ui/neo/badge';
import { Button } from '@/components/ui/neo/button';
import { formatFileSize, formatDuration } from '@/lib/formatters';
import { getAudioFormat } from '@/lib/upload-helpers';
import { Upload } from '@/types';
import { Link, router } from '@inertiajs/react';
import { BarChart3, Clock, Music, Volume2 } from 'lucide-react';

interface BrutalistSimilarTrackCardProps {
    upload: Upload;
    index: number;
}

export const BrutalistSimilarTrackCard = ({ upload, index }: BrutalistSimilarTrackCardProps) => {
    // Cycle through brand colors based on index
    const colorClasses = [
        'bg-neo-green text-neo-black',
        'bg-neo-pink text-neo-white',
        'bg-neo-blue text-neo-white',
        'bg-neo-yellow text-neo-black',
    ];
    const colorClass = colorClasses[index % colorClasses.length];

    const handleCardClick = () => {
        const uploadId = upload?.id || upload?.data?.id;
        if (uploadId) {
            router.visit(route('uploads.show', { upload: uploadId }));
        }
    };

    return (
        <div 
            className={`neo-border neo-shadow ${colorClass} p-4 cursor-pointer neo-transition hover:translate-x-boxShadowX hover:translate-y-boxShadowY hover:shadow-none group`}
            onClick={handleCardClick}
        >
            {/* Header with title */}
            <div className="mb-4">
                <h4 className="font-black uppercase tracking-wide text-sm line-clamp-2 mb-2">
                    {upload.title}
                </h4>
                {upload.artist && (
                    <p className="font-bold text-xs opacity-75 line-clamp-1">
                        BY {upload.artist.toUpperCase()}
                    </p>
                )}
            </div>

            {/* Audio Visualization */}
            <div className="neo-border bg-neo-black p-3 mb-4">
                <div className="flex items-center justify-center space-x-1">
                    {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                        <div
                            key={i}
                            className="w-1 bg-neo-white animate-pulse"
                            style={{
                                height: `${15 + Math.floor(Math.random() * 20)}px`,
                                animationDelay: `${i * 0.15}s`,
                            }}
                        />
                    ))}
                </div>
            </div>

            {/* Analysis Match Indicators */}
            {upload.analysis && (
                <div className="mb-4 space-y-2">
                    <div className="flex flex-wrap gap-1">
                        {upload.analysis.musical_key && (
                            <div className="neo-border bg-neo-black px-2 py-1">
                                <span className="text-xs font-black text-neo-white">
                                    {upload.analysis.musical_key}
                                </span>
                            </div>
                        )}
                        {upload.analysis.bpm && (
                            <div className="neo-border bg-neo-black px-2 py-1">
                                <span className="text-xs font-black text-neo-white">
                                    {upload.analysis.bpm}BPM
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Technical Details */}
            <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-xs font-bold">
                    <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>{formatDuration(upload.duration)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Volume2 className="h-3 w-3" />
                        <span>{formatFileSize(upload.size)}</span>
                    </div>
                </div>
                <div className="flex items-center justify-between text-xs font-bold">
                    <Badge variant="neutral" className="text-xs font-bold">
                        {getAudioFormat(upload.mime_type)}
                    </Badge>
                    {upload.has_analysis && (
                        <Badge variant="neutral" className="text-xs font-bold">
                            <BarChart3 className="h-3 w-3 mr-1" />
                            ANALYZED
                        </Badge>
                    )}
                </div>
            </div>

            {/* Action Button */}
            <div className="flex gap-2">
                {(upload?.id || upload?.data?.id) && (
                    <Link href={route('uploads.show', { upload: upload?.id || upload?.data?.id })} className="flex-1">
                        <Button 
                            variant="neutral" 
                            size="sm" 
                            className="w-full font-black uppercase text-xs neo-transition group-hover:translate-x-1 group-hover:translate-y-1"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <Music className="h-3 w-3 mr-1" />
                            PLAY
                        </Button>
                    </Link>
                )}
                {upload.has_analysis && (upload?.id || upload?.data?.id) && (
                    <Link href={route('uploads.analysis.show', { upload: upload?.id || upload?.data?.id })}>
                        <Button 
                            variant="neutral" 
                            size="sm" 
                            className="font-black uppercase text-xs neo-transition group-hover:translate-x-1 group-hover:translate-y-1"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <BarChart3 className="h-3 w-3" />
                        </Button>
                    </Link>
                )}
            </div>
        </div>
    );
};