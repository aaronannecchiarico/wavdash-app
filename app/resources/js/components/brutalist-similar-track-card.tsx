import { Badge } from '@/components/ui/neo/badge';
import { Button } from '@/components/ui/button';
import { formatDuration, formatFileSize } from '@/lib/formatters';
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
    const colorClasses = ['bg-neo-green text-neo-black', 'bg-neo-pink text-neo-white', 'bg-neo-blue text-neo-white', 'bg-neo-yellow text-neo-black'];
    const colorClass = colorClasses[index % colorClasses.length];

    const handleCardClick = () => {
        if (upload.id) {
            router.visit(route('uploads.show', { upload: upload.id }));
        }
    };

    return (
        <div
            className={`neo-border neo-shadow ${colorClass} neo-transition group cursor-pointer p-4 hover:translate-x-boxShadowX hover:translate-y-boxShadowY hover:shadow-none`}
            onClick={handleCardClick}
        >
            {/* Header with title */}
            <div className="mb-4">
                <h4 className="mb-2 line-clamp-2 text-sm font-black tracking-wide uppercase">{upload.title}</h4>
                {upload.artist && <p className="line-clamp-1 text-xs font-bold opacity-75">BY {upload.artist.toUpperCase()}</p>}
            </div>

            {/* Audio Visualization */}
            <div className="neo-border bg-neo-black mb-4 p-3">
                <div className="flex items-center justify-center space-x-1">
                    {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                        <div
                            key={i}
                            className="bg-neo-white w-1 animate-pulse"
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
                                <span className="text-neo-white text-xs font-black">{upload.analysis.musical_key}</span>
                            </div>
                        )}
                        {upload.analysis.bpm && (
                            <div className="neo-border bg-neo-black px-2 py-1">
                                <span className="text-neo-white text-xs font-black">{upload.analysis.bpm}BPM</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Technical Details */}
            <div className="mb-4 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                    <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>{upload.duration ? formatDuration(upload.duration) : '0:00'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Volume2 className="h-3 w-3" />
                        <span>{formatFileSize(upload.size)}</span>
                    </div>
                </div>
                <div className="flex items-center justify-between text-xs font-bold">
                    <Badge variant="secondary" className="text-xs font-bold">
                        {getAudioFormat(upload.mime_type)}
                    </Badge>
                    {upload.has_analysis && (
                        <Badge variant="secondary" className="text-xs font-bold">
                            <BarChart3 className="mr-1 h-3 w-3" />
                            ANALYZED
                        </Badge>
                    )}
                </div>
            </div>

            {/* Action Button */}
            <div className="flex gap-2">
                {upload.id && (
                    <Link href={route('uploads.show', { upload: upload.id })} className="flex-1">
                        <Button
                            variant="secondary"
                            size="sm"
                            className="neo-transition w-full text-xs font-black uppercase group-hover:translate-x-1 group-hover:translate-y-1"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <Music className="mr-1 h-3 w-3" />
                            PLAY
                        </Button>
                    </Link>
                )}
                {upload.has_analysis && upload.id && (
                    <Link href={route('uploads.analysis.show', { upload: upload.id })}>
                        <Button
                            variant="secondary"
                            size="sm"
                            className="neo-transition text-xs font-black uppercase group-hover:translate-x-1 group-hover:translate-y-1"
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
