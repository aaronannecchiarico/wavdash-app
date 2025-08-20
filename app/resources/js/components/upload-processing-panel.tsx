import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
                <h2 className="text-lg font-semibold text-foreground mb-2">Processing & Analysis</h2>
                <p className="text-sm text-muted-foreground">
                    Enhance your track with advanced audio processing features
                </p>
            </div>
            
            {sections.map((section) => {
                const Icon = section.icon;
                
                return (
                    <Card key={section.id} className="relative">
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                    <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                                    <CardTitle className="text-base">{section.title}</CardTitle>
                                </div>
                                {section.hasResults && (
                                    <Badge variant="secondary" className="text-xs">
                                        Complete
                                    </Badge>
                                )}
                                {section.isProcessing && (
                                    <Badge variant="outline" className="text-xs">
                                        Processing
                                    </Badge>
                                )}
                            </div>
                            <CardDescription className="text-sm">
                                {section.description}
                            </CardDescription>
                        </CardHeader>
                        
                        <CardContent>
                            {section.hasResults && section.resultSummary ? (
                                <div className="space-y-3">
                                    <div className="text-sm">
                                        {section.id === 'analysis' && section.resultSummary && (
                                            <div className="grid grid-cols-2 gap-2 text-xs">
                                                {section.resultSummary.key && (
                                                    <div>
                                                        <span className="font-medium">Key:</span> {section.resultSummary.key}
                                                    </div>
                                                )}
                                                {section.resultSummary.bpm && (
                                                    <div>
                                                        <span className="font-medium">BPM:</span> {Math.round(section.resultSummary.bpm)}
                                                    </div>
                                                )}
                                                {section.resultSummary.loudness && (
                                                    <div className="col-span-2">
                                                        <span className="font-medium">Loudness:</span> {section.resultSummary.loudness}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        
                                        {section.id === 'stems' && section.resultSummary && (
                                            <div className="space-y-1 text-xs">
                                                <div>
                                                    <span className="font-medium">Stems:</span> {section.resultSummary.count} tracks
                                                </div>
                                                <div className="text-muted-foreground">
                                                    {section.resultSummary.types}
                                                </div>
                                            </div>
                                        )}
                                        
                                        {section.id === 'tempo' && section.resultSummary && (
                                            <div className="space-y-1 text-xs">
                                                <div className="flex items-center justify-between">
                                                    <span>
                                                        <span className="font-medium">Variations:</span> {section.resultSummary.count} files
                                                    </span>
                                                    <Link href={route(section.route, upload.id)} className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium">
                                                        View All
                                                    </Link>
                                                </div>
                                                <div className="text-muted-foreground">
                                                    {section.resultSummary.variations}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    
                                    <Link href={route(section.route, upload.id)}>
                                        <Button variant="outline" size="sm" className="w-full">
                                            <Play className="mr-2 h-3 w-3" />
                                            View Details
                                        </Button>
                                    </Link>
                                </div>
                            ) : section.isProcessing ? (
                                <div className="space-y-3">
                                    <p className="text-sm text-muted-foreground">
                                        Processing in progress...
                                    </p>
                                    <Link href={route(section.route, upload.id)}>
                                        <Button variant="outline" size="sm" className="w-full" disabled>
                                            View Progress
                                        </Button>
                                    </Link>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <p className="text-sm text-muted-foreground">
                                        This feature has not been run yet.
                                    </p>
                                    <Link href={route(section.route, upload.id)}>
                                        <Button variant="default" size="sm" className="w-full">
                                            <Icon className="mr-2 h-3 w-3" />
                                            Create {section.title}
                                        </Button>
                                    </Link>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                );
            })}
        </div>
    );
}