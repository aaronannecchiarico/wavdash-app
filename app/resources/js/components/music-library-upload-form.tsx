import InputError from '@/components/input-error';
import { Button } from '@/components/ui/neo/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/neo/card';
import { Input } from '@/components/ui/neo/input';
import { Label } from '@/components/ui/label';
import { NeoProgressBar } from '@/components/ui/neo/progress-bar';
import { Textarea } from '@/components/ui/textarea';
import { type Upload as UploadType } from '@/types';
import { useAudioFileHandler } from '@/hooks/useAudioFileHandler';
import { Loader2, Music, Upload } from 'lucide-react';
import React, { useEffect } from 'react';

export interface UploadFormData {
    title: string;
    description: string;
    audio_file: File | null;
    _method?: 'PUT';
}

interface MusicLibraryUploadFormProps {
    mode: 'create' | 'edit';
    data: UploadFormData;
    setData: (key: keyof UploadFormData | string, value: unknown) => void;
    errors: Partial<Record<keyof UploadFormData, string>>;
    processing: boolean;
    onSubmit: (e: React.FormEvent) => void;
    upload?: UploadType;
    uploadProgress?: number;
    wasSuccessful?: boolean;
    onReset?: () => void;
}

export function MusicLibraryUploadForm({
    mode,
    data,
    setData,
    errors,
    processing,
    onSubmit,
    upload,
    uploadProgress = 0,
    wasSuccessful,
    onReset,
}: MusicLibraryUploadFormProps) {
    const {
        fileMetadata,
        isProcessingFile,
        fileInputRef,
        handleFileChange: handleAudioFileChange,
        resetFileInput
    } = useAudioFileHandler({
        initialTitle: data.title,
        onTitleSuggestion: (title) => setData('title', title)
    });

    useEffect(() => {
        if (wasSuccessful && onReset) {
            resetFileInput();
        }
    }, [wasSuccessful, onReset, resetFileInput]);

    // Set file from existing upload in edit mode
    useEffect(() => {
        if (mode === 'edit' && upload && !fileMetadata) {
            // Let the form know the file is present but don't upload again
            setData('audio_file', null);
        }
    }, [mode, upload, fileMetadata]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleAudioFileChange(e);
        const file = e.target.files?.[0];
        if (file) {
            setData('audio_file', file);
        }
    };

    return (
        <Card>
            <form onSubmit={onSubmit}>
                <CardHeader>
                        <CardTitle className="font-heading font-black uppercase tracking-widest text-foreground">
                            {mode === 'create' ? 'Upload Audio' : 'Edit Audio'}
                        </CardTitle>
                    <CardDescription className="font-bold text-foreground uppercase">
                        {mode === 'create' ? 'Upload an audio file to use in beats and contests.' : 'Update the details for this audio file.'}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="audio_file" className="font-heading font-black uppercase tracking-wide text-foreground">
                            Audio File {mode === 'create' && <span className="text-red-500">*</span>}
                        </Label>
                        <div
                            className={`border-2 border-border bg-chart-3 dark:bg-chart-1 p-8 cursor-pointer hover:bg-chart-2 dark:hover:bg-chart-2 transition-all ${errors.audio_file ? 'border-red-500' : ''}`}
                            style={{ boxShadow: 'var(--shadow)' }}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <div className="text-center space-y-4">
                                <div className="w-24 h-24 mx-auto bg-main-foreground border-2 border-border flex items-center justify-center">
                                    <Upload className="h-12 w-12 text-secondary-background" />
                                </div>
                                
                                <div>
                                    <h3 className="text-2xl font-heading font-black uppercase tracking-widest text-main-foreground mb-2">
                                        DROP YOUR BEATS
                                    </h3>
                                    <p className="font-bold text-main-foreground">
                                        MP3, WAV, AIFF, FLAC • MAX 50MB
                                    </p>
                                </div>
                                
                                {errors.audio_file && (
                                    <div className="border-2 border-border bg-red-500 p-3" style={{ boxShadow: 'var(--shadow)' }}>
                                        <p className="font-heading font-black text-white uppercase">
                                            {errors.audio_file}
                                        </p>
                                    </div>
                                )}
                            </div>
                            
                            <input
                                id="audio_file"
                                ref={fileInputRef}
                                type="file"
                                className="hidden"
                                accept="audio/mpeg,audio/wav,audio/aiff,audio/flac,audio/ogg"
                                onChange={handleFileChange}
                                disabled={processing}
                            />
                        </div>
                        <InputError message={errors.audio_file} />
                    </div>

                    {(isProcessingFile || fileMetadata) && (
                        <div className="space-y-2">
                            <Label className="font-heading font-black uppercase tracking-wide text-foreground">File Details</Label>
                            <div className="border-2 border-border bg-main-foreground p-4" style={{ boxShadow: 'var(--shadow)' }}>
                                {isProcessingFile ? (
                                    <div className="flex items-center text-sm text-secondary-background">
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        <span className="font-bold uppercase">Processing file...</span>
                                    </div>
                                ) : (
                                    fileMetadata && (
                                        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                            <div className="col-span-2 flex items-center space-x-2 font-heading font-black">
                                                <Music className="h-4 w-4 text-chart-1" />
                                                <span className="truncate text-secondary-background uppercase">{fileMetadata.name}</span>
                                            </div>
                                            <div>
                                                <strong className="font-heading font-black text-secondary-background">SIZE:</strong>{' '}
                                                <span className="text-secondary-background font-mono">{fileMetadata.size}</span>
                                            </div>
                                            <div>
                                                <strong className="font-heading font-black text-secondary-background">DURATION:</strong>{' '}
                                                <span className="text-secondary-background font-mono">{fileMetadata.duration}</span>
                                            </div>
                                            <div className="col-span-2">
                                                <strong className="font-heading font-black text-secondary-background">TYPE:</strong>{' '}
                                                <span className="text-secondary-background font-mono">{fileMetadata.type}</span>
                                            </div>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="title" className="font-heading font-black uppercase tracking-wide text-foreground">
                            Title <span className="text-red-500">*</span>
                        </Label>
                        <Input id="title" type="text" value={data.title} onChange={(e) => setData('title', e.target.value)} disabled={processing} />
                        <InputError message={errors.title} />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="description" className="font-heading font-black uppercase tracking-wide text-foreground">Description (Optional)</Label>
                        <Textarea
                            id="description"
                            value={data.description}
                            onChange={(e) => setData('description', e.target.value)}
                            rows={3}
                            disabled={processing}
                        />
                        <InputError message={errors.description} />
                    </div>
                </CardContent>
                {processing && uploadProgress > 0 && (
                    <div className="px-6 pb-4">
                        <div className="border-2 border-border bg-main-foreground p-4" style={{ boxShadow: 'var(--shadow)' }}>
                            <div className="flex justify-between items-center mb-2">
                                <span className="font-heading font-black text-secondary-background uppercase flex items-center">
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Uploading
                                </span>
                                <span className="font-mono text-chart-1">{uploadProgress}%</span>
                            </div>
                            <NeoProgressBar value={uploadProgress} color="bg-chart-1" />
                        </div>
                    </div>
                )}
                <CardFooter className="flex justify-end space-x-4 px-6 py-4">
                    <Button 
                        type="button" 
                        variant="outline" 
                        onClick={() => window.history.back()} 
                        disabled={processing} 
                        className="px-6 py-2 font-heading font-black uppercase tracking-wider"
                    >
                        Cancel
                    </Button>
                    <Button 
                        type="submit" 
                        disabled={processing || isProcessingFile || (mode === 'create' && !data.audio_file)} 
                        className="px-6 py-2 font-heading font-black uppercase tracking-wider"
                    >
                        {processing && uploadProgress === 0 && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {processing ? 'Uploading...' : mode === 'create' ? 'Upload' : 'Save Changes'}
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
}
