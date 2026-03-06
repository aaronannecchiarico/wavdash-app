import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Upload } from '@/types';
import { Link } from '@inertiajs/react';
import { BarChart3, Gauge, Scissors } from 'lucide-react';

interface UploadProcessingPanelProps {
    upload: Upload;
}

export function UploadProcessingPanel({ upload }: UploadProcessingPanelProps) {
    const sections = [
        {
            id: 'analysis',
            title: 'Audio analysis',
            description: 'Analyze musical properties like key, BPM, and timbral characteristics',
            icon: BarChart3,
            route: 'uploads.analysis.show',
            hasResults: upload.has_analysis,
            isProcessing: upload.is_analysis_in_progress,
            resultSummary: upload.analysis
                ? {
                      key: upload.analysis.musical_key,
                      bpm: upload.analysis.bpm,
                      loudness: upload.analysis.loudness_db ? `${upload.analysis.loudness_db.toFixed(1)} dB` : null,
                  }
                : null,
        },
        {
            id: 'stems',
            title: 'Stem separation',
            description: 'Separate audio into individual instrument tracks',
            icon: Scissors,
            route: 'uploads.stems.show',
            hasResults: upload.has_stems,
            isProcessing: upload.is_stem_separation_in_progress,
            resultSummary:
                upload.stems && upload.stems.length > 0
                    ? {
                          count: upload.stems.length,
                          types: upload.stems.map((stem) => stem.stem_type_name || stem.stem_type).join(', '),
                      }
                    : null,
        },
        {
            id: 'tempo',
            title: 'Tempo effects',
            description: 'Generate tempo and pitch variations of your audio',
            icon: Gauge,
            route: 'uploads.tempo.show',
            hasResults: upload.has_tempos,
            isProcessing: upload.is_tempo_processing_in_progress,
            resultSummary:
                upload.tempos && upload.tempos.length > 0
                    ? {
                          count: upload.tempos.length,
                          variations: upload.tempos.map((tempo) => tempo.preset_name || tempo.preset).join(', '),
                      }
                    : null,
        },
    ];

    return (
        <div className="space-y-3">
            {sections.map((section) => {
                const Icon = section.icon;

                const statusVariant = section.hasResults ? 'success' : section.isProcessing ? 'processing' : 'secondary';
                const statusLabel = section.hasResults ? 'Complete' : section.isProcessing ? 'Processing' : 'Available';

                return (
                    <div key={section.id} className="rounded-[--radius-md] border border-[--border] bg-[--surface-1] p-4">
                        <div className="flex items-start gap-3 mb-3">
                            <div className="flex h-9 w-9 items-center justify-center rounded-[--radius-md] bg-[--amber]/10 shrink-0">
                                <Icon className="h-4 w-4 text-[--amber]" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2 mb-0.5">
                                    <h3 className="font-sans font-semibold text-sm text-foreground">{section.title}</h3>
                                    <Badge variant={statusVariant}>{statusLabel}</Badge>
                                </div>
                                <p className="text-xs text-muted-foreground leading-relaxed">{section.description}</p>
                            </div>
                        </div>

                        {section.isProcessing && (
                            <div className="flex items-center gap-2 mb-3">
                                <div className="h-3 w-3 animate-spin rounded-full border-2 border-[--amber] border-t-transparent" />
                                <span className="text-xs text-muted-foreground">Processing...</span>
                            </div>
                        )}

                        {section.hasResults && section.resultSummary && (
                            <div className="mb-3 rounded-[--radius-sm] bg-[--surface-2] px-3 py-2">
                                {section.id === 'analysis' && (
                                    <div className="flex flex-wrap gap-3 text-xs">
                                        {section.resultSummary.key && (
                                            <span>
                                                <span className="text-muted-foreground">Key </span>
                                                <span className="font-mono font-medium text-[--jade]">{section.resultSummary.key}</span>
                                            </span>
                                        )}
                                        {section.resultSummary.bpm && (
                                            <span>
                                                <span className="text-muted-foreground">BPM </span>
                                                <span className="font-mono font-medium text-[--amber]">{Math.round(section.resultSummary.bpm)}</span>
                                            </span>
                                        )}
                                        {section.resultSummary.loudness && (
                                            <span>
                                                <span className="text-muted-foreground">Loudness </span>
                                                <span className="font-mono font-medium text-foreground">{section.resultSummary.loudness}</span>
                                            </span>
                                        )}
                                    </div>
                                )}
                                {section.id === 'stems' && (
                                    <div className="text-xs">
                                        <span className="font-mono font-medium text-foreground">{section.resultSummary.count} tracks</span>
                                        <span className="text-muted-foreground ml-1">— {section.resultSummary.types}</span>
                                    </div>
                                )}
                                {section.id === 'tempo' && (
                                    <div className="text-xs">
                                        <span className="font-mono font-medium text-foreground">{section.resultSummary.count} variations</span>
                                        <span className="text-muted-foreground ml-1">— {section.resultSummary.variations}</span>
                                    </div>
                                )}
                            </div>
                        )}

                        <Button variant={section.hasResults ? 'secondary' : 'default'} size="sm" className="w-full" asChild>
                            <Link href={route(section.route, upload.id)}>
                                {section.hasResults ? 'View results' : 'Start processing'}
                            </Link>
                        </Button>
                    </div>
                );
            })}
        </div>
    );
}
