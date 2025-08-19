import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { AudioPlayer } from '@/components/audio-player';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem, type Upload } from '@/types';
import { Head, useForm, usePage } from '@inertiajs/react';
import { Gauge, Music, Trash2, Wand2, Zap, AlertCircle, Download, Volume2, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface TempoPreset {
    name: string;
    tempo_factor: number;
    pitch_shift_semitones: number;
    preserve_pitch: boolean;
    effects: string[];
    description: string;
}

interface TempoSuggestion {
    preset: string;
    reason: string;
    optimal_factor?: number;
    confidence?: number;
}

interface Props {
    upload: Upload;
    analysis_service: {
        enabled: boolean;
        available: boolean;
    };
    tempo_presets: {
        available_presets: Record<string, TempoPreset>;
        default_preset: string;
        tempo_factor_range: { min: number; max: number };
        pitch_shift_range: { min: number; max: number };
    };
    tempo_suggestions: {
        suggestions: Record<string, TempoSuggestion>;
    };
}

export default function Tempo({ upload, analysis_service, tempo_presets, tempo_suggestions }: Props) {
    const { props } = usePage();
    const flash = props.flash as { success?: string; error?: string } | undefined;
    const uploadData = 'data' in upload && upload.data ? (upload.data as Upload) : upload;

    const { data, setData, post, delete: destroy, processing } = useForm<{
        preset: string;
        tempo_factor: number;
        pitch_shift_semitones: number;
        preserve_pitch: boolean;
        add_reverb: boolean;
        use_stems: boolean;
    }>({
        preset: 'sped_up',
        tempo_factor: 1.25,
        pitch_shift_semitones: 0,
        preserve_pitch: false,
        add_reverb: false,
        use_stems: false,
    });

    const [selectedPreset, setSelectedPreset] = useState<string>('sped_up');
    const [showCreateForm, setShowCreateForm] = useState(false);

    useEffect(() => {
        if (flash?.success) {
            toast.success(flash.success);
        }
        if (flash?.error) {
            toast.error(flash.error);
        }
    }, [flash]);

    const breadcrumbs: BreadcrumbItem[] = [
        {
            title: 'Music Library',
            href: route('uploads.index'),
        },
        {
            title: uploadData.title,
            href: route('uploads.show', { upload: uploadData.id }),
        },
        {
            title: 'Tempo Effects',
            href: route('uploads.tempo.show', { upload: uploadData.id }),
            description: 'Speed up, slow down, and apply tempo effects',
        },
    ];

    const handlePresetChange = (preset: string) => {
        setSelectedPreset(preset);
        setData('preset', preset);
        
        if (preset !== 'custom' && tempo_presets?.available_presets?.[preset]) {
            const presetData = tempo_presets.available_presets[preset];
            setData(prevData => ({
                ...prevData,
                preset,
                tempo_factor: presetData.tempo_factor,
                pitch_shift_semitones: presetData.pitch_shift_semitones,
                preserve_pitch: presetData.preserve_pitch,
                add_reverb: presetData.effects.includes('reverb'),
            }));
        }
    };

    const handleCreateSuccess = () => {
        setShowCreateForm(false);
        // Reset form to defaults
        setData({
            preset: 'sped_up',
            tempo_factor: 1.25,
            pitch_shift_semitones: 0,
            preserve_pitch: false,
            add_reverb: false,
            use_stems: false,
        });
        setSelectedPreset('sped_up');
    };

    const handleStartProcessing = () => {
        post(route('uploads.tempo.store', { upload: uploadData.id }), {
            onSuccess: () => {
                handleCreateSuccess();
            }
        });
    };

    const handleDeleteTempo = () => {
        if (confirm('Are you sure you want to delete all tempo processing data? This action cannot be undone.')) {
            destroy(route('uploads.tempo.destroy', { upload: uploadData.id }));
        }
    };

    const handleDeleteTask = () => {
        if (confirm('Are you sure you want to cancel and delete this tempo processing task? This will stop the processing and allow you to start a new one.')) {
            destroy(route('uploads.tempo.delete-task', { upload: uploadData.id }));
        }
    };

    const getTempoDownloadUrl = (tempo: any) => {
        return route('uploads.tempo.download', { 
            upload: uploadData.id, 
            tempo: tempo.id 
        });
    };

    const handleDownload = (tempo: any) => {
        const downloadUrl = route('uploads.tempo.download', { 
            upload: uploadData.id, 
            tempo: tempo.id 
        });
        window.open(downloadUrl, '_blank');
    };

    const canCreateTempo = () => {
        return analysis_service.enabled && 
               analysis_service.available && 
               uploadData.status === 'ready' &&
               (!uploadData.tempo_task || 
                uploadData.tempo_task.status === 'deleted' || 
                uploadData.tempo_task.status === 'completed' ||
                uploadData.tempo_task.status === 'failed');
    };

    const renderCreateTempoForm = () => {
        if (!analysis_service.enabled) {
            return (
                <div className="text-center py-8 text-muted-foreground">
                    <Gauge className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Audio processing is currently disabled.</p>
                </div>
            );
        }

        if (!analysis_service.available) {
            return (
                <div className="text-center py-8 text-muted-foreground">
                    <Gauge className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Audio processing service is currently unavailable.</p>
                    <p className="text-sm mt-2">Please try again later.</p>
                </div>
            );
        }

        if (uploadData.status !== 'ready') {
            return (
                <div className="text-center py-8 text-muted-foreground">
                    <Gauge className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Upload must be processed before tempo effects can be applied.</p>
                    <p className="text-sm mt-2">Current status: {uploadData.status}</p>
                </div>
            );
        }

        return (
            <div className="space-y-6">
                {/* Preset Selection */}
                <div className="space-y-2">
                    <Label htmlFor="preset">Preset</Label>
                    <Select value={selectedPreset} onValueChange={handlePresetChange}>
                        <SelectTrigger className="w-full">
                            <SelectValue placeholder="Choose a tempo preset" />
                        </SelectTrigger>
                        <SelectContent>
                            {tempo_presets?.available_presets && Object.entries(tempo_presets.available_presets).map(([key, preset]) => (
                                <SelectItem key={key} value={key} className="hover:bg-accent hover:text-accent-foreground">
                                    <div className="flex items-center justify-between w-full">
                                        <span className="font-medium">{preset.name}</span>
                                        <span className="text-xs text-muted-foreground ml-2 opacity-70">x{preset.tempo_factor}</span>
                                    </div>
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {/* Smart Suggestions */}
                {tempo_suggestions?.suggestions && Object.keys(tempo_suggestions.suggestions).length > 0 && (
                    <div className="space-y-2">
                        <Label>Smart Suggestions</Label>
                        <div className="grid gap-2">
                            {Object.entries(tempo_suggestions.suggestions).map(([key, suggestion]) => (
                                <Card key={key} className="p-3 cursor-pointer hover:bg-muted/50 border-border/50 hover:border-border transition-colors" onClick={() => handlePresetChange(suggestion.preset)}>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="font-medium text-foreground">{suggestion.preset.replace('_', ' ').toUpperCase()}</p>
                                            <p className="text-xs text-muted-foreground">{suggestion.reason}</p>
                                        </div>
                                        <Wand2 className="h-4 w-4 text-primary" />
                                    </div>
                                </Card>
                            ))}
                        </div>
                    </div>
                )}

                {/* Custom Options */}
                {selectedPreset === 'custom' && (
                    <div className="space-y-4 border-t border-border/50 pt-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="tempo_factor">Tempo Factor</Label>
                                <Input
                                    id="tempo_factor"
                                    type="number"
                                    step="0.1"
                                    min={tempo_presets?.tempo_factor_range?.min || 0.25}
                                    max={tempo_presets?.tempo_factor_range?.max || 4.0}
                                    value={data.tempo_factor}
                                    onChange={(e) => setData('tempo_factor', parseFloat(e.target.value))}
                                    className="bg-background"
                                />
                                <p className="text-xs text-muted-foreground">
                                    1.0 = original speed, &gt;1.0 = faster, &lt;1.0 = slower
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="pitch_shift">Pitch Shift (semitones)</Label>
                                <Input
                                    id="pitch_shift"
                                    type="number"
                                    step="0.5"
                                    min={tempo_presets?.pitch_shift_range?.min || -12}
                                    max={tempo_presets?.pitch_shift_range?.max || 12}
                                    value={data.pitch_shift_semitones}
                                    onChange={(e) => setData('pitch_shift_semitones', parseFloat(e.target.value))}
                                    className="bg-background"
                                />
                                <p className="text-xs text-muted-foreground">
                                    0 = original pitch, + = higher, - = lower
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Processing Options */}
                <div className="space-y-4 border-t border-border/50 pt-4">
                    <Label>Processing Options</Label>
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="preserve_pitch"
                                checked={data.preserve_pitch}
                                onCheckedChange={(checked) => setData('preserve_pitch', !!checked)}
                            />
                            <Label htmlFor="preserve_pitch" className="text-sm">
                                Preserve original pitch (time-stretch only)
                            </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="add_reverb"
                                checked={data.add_reverb}
                                onCheckedChange={(checked) => setData('add_reverb', !!checked)}
                            />
                            <Label htmlFor="add_reverb" className="text-sm">
                                Add reverb effect
                            </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="use_stems"
                                checked={data.use_stems}
                                onCheckedChange={(checked) => setData('use_stems', !!checked)}
                            />
                            <Label htmlFor="use_stems" className="text-sm">
                                High quality processing (uses stems)
                            </Label>
                        </div>
                    </div>
                </div>

                <div className="flex gap-2">
                    <Button onClick={handleStartProcessing} disabled={processing} className="flex-1">
                        <Zap className="h-4 w-4 mr-2" />
                        {processing ? 'Processing...' : 'Start Processing'}
                    </Button>
                    <Button variant="outline" onClick={() => setShowCreateForm(false)} disabled={processing}>
                        Cancel
                    </Button>
                </div>
            </div>
        );
    };

    const renderTempoProcessingStatus = () => {
        if (uploadData.tempo_task && uploadData.tempo_task.status === 'processing' || uploadData.tempo_task?.status === 'pending') {
            return (
                <Card className="border-border/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Gauge className="h-5 w-5 animate-spin" />
                            Tempo Processing in Progress
                        </CardTitle>
                        <CardDescription>
                            Your audio is being processed with tempo effects. You'll receive a notification when it's complete.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-center py-8">
                            <div className="flex flex-col items-center space-y-4">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                                <div className="text-center">
                                    <p className="text-sm font-medium">Processing tempo effects...</p>
                                    <p className="text-xs text-muted-foreground">
                                        Started {new Date(uploadData.tempo_task.submitted_at).toLocaleString()}
                                    </p>
                                    {uploadData.tempo_task.processing_options && (
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Preset: {uploadData.tempo_task.processing_options.preset || 'Custom'}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-center">
                            <Button variant="outline" onClick={handleDeleteTask} disabled={processing}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Cancel Processing
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            );
        }

        if (uploadData.tempo_task && uploadData.tempo_task.status === 'failed') {
            return (
                <Card className="border-destructive/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertCircle className="h-5 w-5 text-destructive" />
                            Processing Failed
                        </CardTitle>
                        <CardDescription>
                            The tempo processing failed. You can try again or contact support.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="text-center py-4">
                            <p className="text-sm text-muted-foreground mb-4">
                                {uploadData.tempo_task.error_message || 'An error occurred during processing.'}
                            </p>
                            <div className="flex gap-2 justify-center">
                                <Button onClick={handleDeleteTask} disabled={processing}>
                                    <Trash2 className="h-4 w-4 mr-2" />
                                    Clear Failed Task
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            );
        }

        return null;
    };

    const renderExistingTempos = () => {
        if (!uploadData.tempos || uploadData.tempos.length === 0) {
            return null;
        }

        return (
            <Card className="border-border/50">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Gauge className="h-5 w-5 text-success" />
                        Tempo Effects
                    </CardTitle>
                    <CardDescription>
                        Your tempo variations are ready for playback and download.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="space-y-4">
                        <Label>Processed Variations ({uploadData.tempos.length})</Label>
                        <div className="grid gap-4">
                            {uploadData.tempos.map((tempo: any) => (
                                <Card key={tempo.id} className="group hover:shadow-md transition-all duration-200 border border-border/50 hover:border-border bg-card">
                                    <CardContent className="p-6">
                                        <div className="space-y-4">
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <h4 className="font-semibold text-lg text-foreground">{tempo.preset_name || tempo.preset}</h4>
                                                        <Badge variant="secondary" className="text-xs">
                                                            x{tempo.tempo_factor}
                                                        </Badge>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground mb-3">
                                                        {tempo.tempo_description} • {tempo.pitch_description}
                                                    </p>
                                                    <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                                                        {tempo.final_bpm && (
                                                            <span className="flex items-center gap-1">
                                                                <Gauge className="h-3 w-3" />
                                                                {Math.round(tempo.final_bpm)} BPM
                                                            </span>
                                                        )}
                                                        {tempo.formatted_file_size && (
                                                            <span className="flex items-center gap-1">
                                                                <Volume2 className="h-3 w-3" />
                                                                {tempo.formatted_file_size}
                                                            </span>
                                                        )}
                                                        {tempo.formatted_duration && (
                                                            <span className="flex items-center gap-1">
                                                                <Music className="h-3 w-3" />
                                                                {tempo.formatted_duration}
                                                            </span>
                                                        )}
                                                        {tempo.processing_metadata?.quality_score && (
                                                            <span className="flex items-center gap-1">
                                                                <span className="text-xs">📊</span>
                                                                Quality: {Math.round(tempo.processing_metadata.quality_score * 100)}%
                                                            </span>
                                                        )}
                                                    </div>
                                                    
                                                    {/* Processing Warnings */}
                                                    {tempo.processing_metadata?.processing_warnings && tempo.processing_metadata.processing_warnings.length > 0 && (
                                                        <div className="mt-2 p-2 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/30 rounded-md">
                                                            <div className="flex items-start gap-2">
                                                                <AlertCircle className="h-3 w-3 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                                                                <div className="text-xs">
                                                                    <p className="font-medium text-amber-800 dark:text-amber-200 mb-1">Processing Notes:</p>
                                                                    <ul className="text-amber-700 dark:text-amber-300 space-y-0.5">
                                                                        {tempo.processing_metadata.processing_warnings.map((warning: string, index: number) => (
                                                                            <li key={index}>• {warning}</li>
                                                                        ))}
                                                                    </ul>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleDownload(tempo)}
                                                    className="shrink-0 ml-4"
                                                >
                                                    <Download className="h-4 w-4 mr-2" />
                                                    Download
                                                </Button>
                                            </div>
                                            
                                            {/* Audio Player */}
                                            <div className="pt-2 border-t border-border/50">
                                                <AudioPlayer
                                                    url={getTempoDownloadUrl(tempo)}
                                                    title={tempo.preset_name || tempo.preset}
                                                    className="w-full"
                                                />
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                    <div className="flex gap-2 pt-4 border-t border-border/50">
                        <Button onClick={handleDeleteTempo} variant="outline" disabled={processing}>
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete All Tempos
                        </Button>
                    </div>
                </CardContent>
            </Card>
        );
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Tempo Effects - ${uploadData.title}`} />
            
            <div className="container mx-auto px-4 py-8">
                <div className="max-w-4xl mx-auto">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold tracking-tight">Tempo Effects</h1>
                        <p className="text-muted-foreground mt-2">
                            Create viral-ready tempo variations like sped-up, slowed + reverb, nightcore, and more.
                        </p>
                    </div>

                    {/* Upload Info */}
                    <Card className="mb-6 border-border/50">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Music className="h-5 w-5" />
                                {uploadData.title}
                            </CardTitle>
                            <CardDescription className="flex items-center gap-4">
                                <Badge variant="secondary">{uploadData.status}</Badge>
                                {uploadData.analysis && (
                                    <>
                                        <span>Key: {uploadData.analysis.musical_key || 'Unknown'}</span>
                                        <span>BPM: {uploadData.analysis.bpm || 'Unknown'}</span>
                                    </>
                                )}
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <div className="space-y-6">
                        {/* Processing Status */}
                        {renderTempoProcessingStatus()}

                        {/* Existing Tempos */}
                        {renderExistingTempos()}

                        {/* Create New Tempo */}
                        {canCreateTempo() && (
                            <Card className="border-border/50">
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle className="flex items-center gap-2">
                                                <Plus className="h-5 w-5" />
                                                Create New Tempo Effect
                                            </CardTitle>
                                            <CardDescription>
                                                Add another tempo variation to your collection.
                                            </CardDescription>
                                        </div>
                                        {!showCreateForm && (
                                            <Button onClick={() => setShowCreateForm(true)} className="shrink-0">
                                                <Plus className="h-4 w-4 mr-2" />
                                                Create New
                                            </Button>
                                        )}
                                    </div>
                                </CardHeader>
                                {showCreateForm && (
                                    <CardContent>
                                        {renderCreateTempoForm()}
                                    </CardContent>
                                )}
                            </Card>
                        )}

                        {/* Service Unavailable Message */}
                        {!canCreateTempo() && !uploadData.tempos?.length && (
                            <Card className="border-border/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Gauge className="h-5 w-5" />
                                        Tempo Effects
                                    </CardTitle>
                                    <CardDescription>
                                        Create sped-up, slowed-down, or custom tempo variations of your audio.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {renderCreateTempoForm()}
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}