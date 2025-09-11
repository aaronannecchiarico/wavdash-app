import InputError from '@/components/input-error';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/neo/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/neo/card';
import { Input } from '@/components/ui/neo/input';
import { NeoProgressBar } from '@/components/ui/neo/progress-bar';
import { Textarea } from '@/components/ui/textarea';
import { useAudioFileHandler } from '@/hooks/useAudioFileHandler';
import { useClientAudioProcessing } from '@/hooks/useClientAudioProcessing';
import { checkMediaBunnySupport } from '@/lib/browser-support';
import { formatFileSize } from '@/lib/formatters';
import { type Upload as UploadType } from '@/types';
import { Loader2, Music, Upload } from 'lucide-react';
import React, { useEffect, useState } from 'react';

export interface UploadFormData {
    title: string;
    description: string;
    audio_file: File | null;
    _method?: 'PUT';
    client_processed?: boolean;
    original_filename?: string;
    original_size?: number;
    duration?: number;
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
    onProcessedFile?: (data: {
        processedFile: File;
        originalFilename: string;
        originalSize: number;
        duration: number;
    } | null) => void;
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
    onProcessedFile,
}: MusicLibraryUploadFormProps) {
    const {
        fileMetadata,
        isProcessingFile,
        fileInputRef,
        handleFileChange: handleAudioFileChange,
        resetFileInput,
    } = useAudioFileHandler({
        initialTitle: data.title,
        onTitleSuggestion: (title) => setData('title', title),
    });

    const {
        processAudioFile,
        progress: processingProgress,
        error: processingError,
        isProcessing,
    } = useClientAudioProcessing();
    
    const [processedFile, setProcessedFile] = useState<File | null>(null);
    const [originalFileData, setOriginalFileData] = useState<{
        name: string;
        size: number;
        duration: number;
    } | null>(null);

    // Check if client-side processing is enabled (placeholder for feature flag)
    const clientSideProcessingEnabled = true; // TODO: Replace with actual feature flag
    const { supported: browserSupportsProcessing } = checkMediaBunnySupport();

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
    }, [mode, upload, fileMetadata, setData]);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Always run the existing audio file metadata extraction
        handleAudioFileChange(e);

        // Process file on client if supported and enabled
        if (browserSupportsProcessing && clientSideProcessingEnabled) {
            try {
                const result = await processAudioFile(file);
                setProcessedFile(result.processedFile);
                setOriginalFileData({
                    name: file.name,
                    size: file.size,
                    duration: result.duration,
                });
                setData('audio_file', result.processedFile);
                
                // Notify parent component about the processed file
                onProcessedFile?.({
                    processedFile: result.processedFile,
                    originalFilename: file.name,
                    originalSize: file.size,
                    duration: result.duration,
                });
            } catch (error) {
                console.error('Client processing failed, using original file:', error);
                setData('audio_file', file); // Fallback to server processing
                onProcessedFile?.(null); // Clear processed file data
            }
        } else {
            setData('audio_file', file); // Server processing
            onProcessedFile?.(null); // Clear processed file data
        }
    };

    return (
        <Card>
            <form onSubmit={onSubmit}>
                <CardHeader>
                    <CardTitle className="font-heading font-black tracking-widest text-foreground uppercase">
                        {mode === 'create' ? 'Upload Audio' : 'Edit Audio'}
                    </CardTitle>
                    <CardDescription className="font-bold text-foreground uppercase">
                        {mode === 'create' ? 'Upload an audio file to use in beats and contests.' : 'Update the details for this audio file.'}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="audio_file" className="font-heading font-black tracking-wide text-foreground uppercase">
                            Audio File {mode === 'create' && <span className="text-red-500">*</span>}
                        </Label>
                        <div
                            className={`cursor-pointer border-2 border-border bg-chart-3 p-8 transition-all hover:bg-chart-2 dark:bg-chart-1 dark:hover:bg-chart-2 ${errors.audio_file ? 'border-red-500' : ''}`}
                            style={{ boxShadow: 'var(--shadow)' }}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <div className="space-y-4 text-center">
                                <div className="mx-auto flex h-24 w-24 items-center justify-center border-2 border-border bg-main-foreground">
                                    <Upload className="h-12 w-12 text-secondary-background" />
                                </div>

                                <div>
                                    <h3 className="mb-2 font-heading text-2xl font-black tracking-widest text-main-foreground uppercase">
                                        DROP YOUR BEATS
                                    </h3>
                                    <p className="font-bold text-main-foreground">MP3, WAV, AIFF, FLAC • MAX 50MB</p>
                                </div>

                                {errors.audio_file && (
                                    <div className="border-2 border-border bg-red-500 p-3" style={{ boxShadow: 'var(--shadow)' }}>
                                        <p className="font-heading font-black text-white uppercase">{errors.audio_file}</p>
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
                            <Label className="font-heading font-black tracking-wide text-foreground uppercase">File Details</Label>
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
                                                <span className="font-mono text-secondary-background">{fileMetadata.size}</span>
                                            </div>
                                            <div>
                                                <strong className="font-heading font-black text-secondary-background">DURATION:</strong>{' '}
                                                <span className="font-mono text-secondary-background">{fileMetadata.duration}</span>
                                            </div>
                                            <div className="col-span-2">
                                                <strong className="font-heading font-black text-secondary-background">TYPE:</strong>{' '}
                                                <span className="font-mono text-secondary-background">{fileMetadata.type}</span>
                                            </div>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    )}

                    {/* Show processing progress */}
                    {isProcessing && (
                        <div className="space-y-2">
                            <div className="border-2 border-border bg-main-foreground p-4" style={{ boxShadow: 'var(--shadow)' }}>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="font-heading font-black text-secondary-background uppercase">
                                        Converting Audio...
                                    </span>
                                    <span className="font-mono text-chart-1">{processingProgress}%</span>
                                </div>
                                <NeoProgressBar value={processingProgress} color="bg-chart-1" />
                            </div>
                        </div>
                    )}
                    
                    {/* Show file comparison if processed */}
                    {processedFile && originalFileData && (
                        <div className="space-y-2">
                            <div className="border-2 border-border bg-green-100 p-4" style={{ boxShadow: 'var(--shadow)' }}>
                                <div className="text-sm text-green-700">
                                    <div className="font-heading font-black uppercase mb-2">✅ Audio Processed Successfully</div>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div>
                                            <strong>Original:</strong> {originalFileData.name}
                                        </div>
                                        <div>
                                            <strong>Processed:</strong> {processedFile.name}
                                        </div>
                                        <div>
                                            <strong>Size:</strong> {formatFileSize(originalFileData.size)} → {formatFileSize(processedFile.size)}
                                        </div>
                                        <div>
                                            <strong>Format:</strong> OGG Vorbis (128kbps)
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Show processing error if any */}
                    {processingError && (
                        <div className="space-y-2">
                            <div className="border-2 border-border bg-red-100 p-4" style={{ boxShadow: 'var(--shadow)' }}>
                                <div className="text-sm text-red-700">
                                    <div className="font-heading font-black uppercase mb-2">⚠️ Processing Failed</div>
                                    <div className="text-xs">{processingError}</div>
                                    <div className="text-xs mt-2">Falling back to server-side processing.</div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="title" className="font-heading font-black tracking-wide text-foreground uppercase">
                            Title <span className="text-red-500">*</span>
                        </Label>
                        <Input id="title" type="text" value={data.title} onChange={(e) => setData('title', e.target.value)} disabled={processing} />
                        <InputError message={errors.title} />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="description" className="font-heading font-black tracking-wide text-foreground uppercase">
                            Description (Optional)
                        </Label>
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
                            <div className="mb-2 flex items-center justify-between">
                                <span className="flex items-center font-heading font-black text-secondary-background uppercase">
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
                        variant="neutral"
                        onClick={() => window.history.back()}
                        disabled={processing}
                        className="px-6 py-2 font-heading font-black tracking-wider uppercase"
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        disabled={processing || isProcessingFile || (mode === 'create' && !data.audio_file)}
                        className="px-6 py-2 font-heading font-black tracking-wider uppercase"
                    >
                        {processing && uploadProgress === 0 && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {processing ? 'Uploading...' : mode === 'create' ? 'Upload' : 'Save Changes'}
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
}
