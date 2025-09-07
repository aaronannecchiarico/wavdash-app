import { Badge } from '@/components/ui/neo/badge';
import { Button } from '@/components/ui/neo/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/neo/card';
import { Upload } from '@/types';
import { Link } from '@inertiajs/react';
import { BarChart3, Gauge, Play, Scissors } from 'lucide-react';

interface UploadProcessingPanelProps {
    upload: Upload;
}

export function UploadProcessingPanel({ upload }: UploadProcessingPanelProps) {
    const sections = [
        {
            id: 'analysis',
            title: 'Audio Analysis',
            description: 'Analyze musical properties like key, BPM, and timbral characteristics',
            icon: BarChart3,
            route: 'uploads.analysis.show',
            hasResults: upload.has_analysis,
            isProcessing: upload.is_analysis_in_progress,
            resultSummary: upload.analysis ? {
                key: upload.analysis.musical_key,
                bpm: upload.analysis.bpm,
                loudness: upload.analysis.loudness_db ? `${upload.analysis.loudness_db.toFixed(1)} dB` : null,
            } : null,
        },
        {
            id: 'stems',
            title: 'Stem Separation',
            description: 'Separate audio into individual instrument tracks',
            icon: Scissors,
            route: 'uploads.stems.show',
            hasResults: upload.has_stems,
            isProcessing: upload.is_stem_separation_in_progress,
            resultSummary: upload.stems && upload.stems.length > 0 ? {
                count: upload.stems.length,
                types: upload.stems.map(stem => stem.stem_type_name || stem.stem_type).join(', '),
            } : null,
        },
        {
            id: 'tempo',
            title: 'Tempo Effects',
            description: 'Generate tempo and pitch variations of your audio',
            icon: Gauge,
            route: 'uploads.tempo.show',
            hasResults: upload.has_tempos,
            isProcessing: upload.is_tempo_processing_in_progress,
            resultSummary: upload.tempos && upload.tempos.length > 0 ? {
                count: upload.tempos.length,
                variations: upload.tempos.map(tempo => tempo.preset_name || tempo.preset).join(', '),
            } : null,
        },
    ];

    return (
        <div className="space-y-4">
            <div className="mb-6">
                <h2 className="text-lg font-heading font-black uppercase tracking-widest text-foreground mb-2">Processing & Analysis</h2>
                <p className="text-sm font-bold text-foreground uppercase">
                    Enhance your track with advanced audio processing features
                </p>
            </div>
            
            {sections.map((section) => {
                const Icon = section.icon;
                
                const getStatusColor = () => {
                    if (section.hasResults) return 'bg-chart-1'
                    if (section.isProcessing) return 'bg-chart-3'
                    return 'bg-chart-2'
                };
                
                const getStatusText = () => {
                    if (section.hasResults) return 'COMPLETE'
                    if (section.isProcessing) return 'PROCESSING'
                    return 'AVAILABLE'
                };
                
                return (
                    <div key={section.id} className={`border-2 border-border p-6 ${getStatusColor()}`} style={{ boxShadow: 'var(--shadow)' }}>
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center space-x-3">
                                <div className="w-12 h-12 bg-main-foreground border-2 border-border flex items-center justify-center">
                                    <Icon className="h-6 w-6 text-secondary-background" />
                                </div>
                                <div>
                                    <h3 className="font-heading font-black uppercase tracking-wide text-main-foreground">
                                        {section.title}
                                    </h3>
                                    <p className="font-bold text-main-foreground text-sm">
                                        {section.description.toUpperCase()}
                                    </p>
                                </div>
                            </div>
                            
                            <div className="border-2 border-border bg-main-foreground px-3 py-1">
                                <span className="font-heading font-black text-xs text-secondary-background">
                                    {getStatusText()}
                                </span>
                            </div>
                        </div>
                        
                        {section.isProcessing && (
                            <div className="mb-4">
                                <div className="flex items-center space-x-2">
                                    <div className="animate-spin w-4 h-4 border-2 border-main-foreground border-t-transparent rounded-full" />
                                    <span className="font-bold text-main-foreground">PROCESSING...</span>
                                </div>
                            </div>
                        )}
                        
                        {section.hasResults && section.resultSummary && (
                            <div className="mb-4 space-y-2">
                                {section.id === 'analysis' && (
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        {section.resultSummary.key && (
                                            <div>
                                                <span className="font-heading font-black text-main-foreground">KEY:</span> <span className="font-mono text-main-foreground">{section.resultSummary.key}</span>
                                            </div>
                                        )}
                                        {section.resultSummary.bpm && (
                                            <div>
                                                <span className="font-heading font-black text-main-foreground">BPM:</span> <span className="font-mono text-main-foreground">{Math.round(section.resultSummary.bpm)}</span>
                                            </div>
                                        )}
                                        {section.resultSummary.loudness && (
                                            <div className="col-span-2">
                                                <span className="font-heading font-black text-main-foreground">LOUDNESS:</span> <span className="font-mono text-main-foreground">{section.resultSummary.loudness}</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                                
                                {section.id === 'stems' && (
                                    <div className="space-y-1 text-xs">
                                        <div>
                                            <span className="font-heading font-black text-main-foreground">STEMS:</span> <span className="font-mono text-main-foreground">{section.resultSummary.count} tracks</span>
                                        </div>
                                        <div className="font-mono text-main-foreground text-xs">
                                            {section.resultSummary.types}
                                        </div>
                                    </div>
                                )}
                                
                                {section.id === 'tempo' && (
                                    <div className="space-y-1 text-xs">
                                        <div>
                                            <span className="font-heading font-black text-main-foreground">VARIATIONS:</span> <span className="font-mono text-main-foreground">{section.resultSummary.count} files</span>
                                        </div>
                                        <div className="font-mono text-main-foreground text-xs">
                                            {section.resultSummary.variations}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        
                        <Button 
                            variant="outline" 
                            className="w-full font-heading font-black uppercase border-main-foreground text-main-foreground hover:bg-main-foreground hover:text-secondary-background"
                            asChild
                        >
                            <Link href={route(section.route, upload.id)}>
                                {section.hasResults ? 'VIEW RESULTS' : 'START PROCESS'}
                            </Link>
                        </Button>
                    </div>
                );
            })}
        </div>
    );
}