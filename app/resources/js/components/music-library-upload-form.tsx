import InputError from '@/components/input-error';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { useAudioFileHandler } from '@/hooks/useAudioFileHandler';
import { useClientAudioProcessing } from '@/hooks/useClientAudioProcessing';
import { checkMediaBunnySupport } from '@/lib/browser-support';
import { formatFileSize } from '@/lib/formatters';
import { type Upload as UploadType } from '@/types';
import { AlertCircle, CheckCircle2, Info, Loader2, Music, Upload } from 'lucide-react';
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
    processing_time_ms?: number;
}

interface AudioProcessingConfig {
    client_side_processing_enabled: boolean;
    ab_test_enabled: boolean;
    should_use_client_processing: boolean;
    fallback_on_error: boolean;
    monitor_performance: boolean;
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
        processingTimeMs: number;
    } | null) => void;
    audioProcessingConfig?: AudioProcessingConfig;
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
    audioProcessingConfig,
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
    const [fallbackReason, setFallbackReason] = useState<string | null>(null);

    const shouldUseClientProcessing = audioProcessingConfig?.should_use_client_processing ?? false;
    const fallbackOnError = audioProcessingConfig?.fallback_on_error ?? true;
    const { supported: browserSupportsProcessing, missingFeatures } = checkMediaBunnySupport();

    useEffect(() => {
        if (wasSuccessful && onReset) {
            resetFileInput();
        }
    }, [wasSuccessful, onReset, resetFileInput]);

    useEffect(() => {
        if (mode === 'edit' && upload && !fileMetadata) {
            setData('audio_file', null);
        }
    }, [mode, upload, fileMetadata, setData]);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        handleAudioFileChange(e);
        setFallbackReason(null);
        setProcessedFile(null);
        setOriginalFileData(null);

        if (!shouldUseClientProcessing) {
            setFallbackReason('Server-side processing selected by A/B test');
            setData('audio_file', file);
            onProcessedFile?.(null);
            return;
        }

        if (!browserSupportsProcessing) {
            setFallbackReason(`Browser missing required features: ${missingFeatures.join(', ')}`);
            setData('audio_file', file);
            onProcessedFile?.(null);
            return;
        }

        try {
            const startTime = Date.now();
            const result = await processAudioFile(file);
            const processingTimeMs = Date.now() - startTime;

            setProcessedFile(result.processedFile);
            setOriginalFileData({ name: file.name, size: file.size, duration: result.duration });
            setData('audio_file', result.processedFile);
            setData('client_processed', true);
            setData('original_filename', file.name);
            setData('original_size', file.size);
            setData('duration', result.duration);
            setData('processing_time_ms', processingTimeMs);
            onProcessedFile?.({
                processedFile: result.processedFile,
                originalFilename: file.name,
                originalSize: file.size,
                duration: result.duration,
                processingTimeMs,
            });
        } catch (error) {
            console.error('Client processing failed:', error);
            if (fallbackOnError) {
                setFallbackReason(`Client processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
                setData('audio_file', file);
                onProcessedFile?.(null);
            }
        }
    };

    return (
        <Card>
            <form onSubmit={onSubmit}>
                <CardHeader>
                    <CardTitle>
                        {mode === 'create' ? 'Upload audio' : 'Edit audio'}
                    </CardTitle>
                    <CardDescription>
                        {mode === 'create'
                            ? 'Upload an audio file to use in beats and contests.'
                            : 'Update the details for this audio file.'}
                    </CardDescription>
                </CardHeader>

                <CardContent className="space-y-5">
                    {/* File drop zone */}
                    <div className="space-y-1.5">
                        <Label htmlFor="audio_file">
                            Audio file {mode === 'create' && <span className="text-destructive ml-0.5">*</span>}
                        </Label>
                        <div
                            className={`cursor-pointer rounded-[--radius-lg] border-2 border-dashed p-8 text-center transition-colors hover:bg-muted ${
                                errors.audio_file ? 'border-destructive' : 'border-[--border-strong] hover:border-[--amber]'
                            }`}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <div className="flex flex-col items-center gap-3">
                                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[--amber]/10">
                                    <Upload className="h-6 w-6 text-[--amber]" />
                                </div>
                                <div>
                                    <p className="font-medium text-sm text-foreground mb-1">
                                        Drop your audio file here
                                    </p>
                                    <p className="text-xs text-muted-foreground">MP3, WAV, AIFF, FLAC — max 50MB</p>
                                </div>
                            </div>

                            {errors.audio_file && (
                                <div className="mt-3 rounded-[--radius-md] border border-destructive/20 bg-destructive/10 px-3 py-2">
                                    <p className="text-xs text-destructive">{errors.audio_file}</p>
                                </div>
                            )}

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

                    {/* File metadata */}
                    {(isProcessingFile || fileMetadata) && (
                        <div className="rounded-[--radius-md] border border-[--border] bg-[--surface-2] p-4">
                            {isProcessingFile ? (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span>Reading file...</span>
                                </div>
                            ) : (
                                fileMetadata && (
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <Music className="h-4 w-4 text-[--amber] shrink-0" />
                                            <span className="text-sm font-medium text-foreground truncate">{fileMetadata.name}</span>
                                        </div>
                                        <div className="grid grid-cols-3 gap-3 text-xs text-muted-foreground">
                                            <div><span className="font-medium text-foreground">Size</span> {fileMetadata.size}</div>
                                            <div><span className="font-medium text-foreground">Duration</span> {fileMetadata.duration}</div>
                                            <div><span className="font-medium text-foreground">Type</span> {fileMetadata.type}</div>
                                        </div>
                                    </div>
                                )
                            )}
                        </div>
                    )}

                    {/* Client processing progress */}
                    {isProcessing && (
                        <div className="rounded-[--radius-md] border border-[--border] bg-[--surface-2] p-4 space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <span className="font-medium text-foreground">Converting audio...</span>
                                <span className="font-mono text-[--amber]">{processingProgress}%</span>
                            </div>
                            <Progress value={processingProgress} className="[&_[data-slot=progress-indicator]]:bg-[--amber]" />
                        </div>
                    )}

                    {/* Processing success */}
                    {processedFile && originalFileData && (
                        <div className="rounded-[--radius-md] border border-green-200 bg-green-50 px-4 py-3 dark:bg-green-900/20 dark:border-green-800">
                            <div className="flex items-start gap-2">
                                <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0 mt-0.5 dark:text-green-400" />
                                <div className="text-xs">
                                    <p className="font-medium text-green-800 dark:text-green-200 mb-1">Audio processed successfully</p>
                                    <p className="text-green-700 dark:text-green-300">
                                        {formatFileSize(originalFileData.size)} → {formatFileSize(processedFile.size)} · OGG Vorbis 128kbps
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Processing error */}
                    {processingError && (
                        <div className="rounded-[--radius-md] border border-amber-200 bg-amber-50 px-4 py-3 dark:bg-amber-900/20 dark:border-amber-800">
                            <div className="flex items-start gap-2">
                                <AlertCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5 dark:text-amber-400" />
                                <div className="text-xs">
                                    <p className="font-medium text-amber-800 dark:text-amber-200 mb-1">Processing failed</p>
                                    <p className="text-amber-700 dark:text-amber-300">{processingError}</p>
                                    <p className="text-amber-600 dark:text-amber-400 mt-1">
                                        {fallbackOnError
                                            ? 'Falling back to server-side processing.'
                                            : 'Please use Chrome or Edge and try again.'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Fallback info */}
                    {fallbackReason && (
                        <div className="rounded-[--radius-md] border border-[--border] bg-[--surface-2] px-4 py-3">
                            <div className="flex items-start gap-2">
                                <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                                <div className="text-xs">
                                    <p className="font-medium text-foreground mb-1">Using server processing</p>
                                    <p className="text-muted-foreground">Your file will be processed on our servers after upload.</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* A/B test info (dev only) */}
                    {audioProcessingConfig?.ab_test_enabled && (
                        <div className="rounded-[--radius-md] border border-[--border] bg-[--surface-2] px-4 py-3">
                            <p className="text-xs text-muted-foreground">
                                A/B test active · {shouldUseClientProcessing ? 'Client-side' : 'Server-side'} processing ·
                                Browser {browserSupportsProcessing ? 'supported' : 'unsupported'}
                            </p>
                        </div>
                    )}

                    {/* Title */}
                    <div className="space-y-1.5">
                        <Label htmlFor="title">
                            Title <span className="text-destructive">*</span>
                        </Label>
                        <Input
                            id="title"
                            type="text"
                            value={data.title}
                            onChange={(e) => setData('title', e.target.value)}
                            disabled={processing}
                            placeholder="Track title"
                        />
                        <InputError message={errors.title} />
                    </div>

                    {/* Description */}
                    <div className="space-y-1.5">
                        <Label htmlFor="description">Description (optional)</Label>
                        <Textarea
                            id="description"
                            value={data.description}
                            onChange={(e) => setData('description', e.target.value)}
                            rows={3}
                            disabled={processing}
                            placeholder="Add a description..."
                        />
                        <InputError message={errors.description} />
                    </div>
                </CardContent>

                {/* Upload progress */}
                {processing && uploadProgress > 0 && (
                    <div className="px-6 pb-4">
                        <div className="rounded-[--radius-md] border border-[--border] bg-[--surface-2] p-4 space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2">
                                    <Loader2 className="h-4 w-4 animate-spin text-[--amber]" />
                                    <span className="font-medium text-foreground">Uploading</span>
                                </div>
                                <span className="font-mono text-[--amber]">{uploadProgress}%</span>
                            </div>
                            <Progress value={uploadProgress} className="[&_[data-slot=progress-indicator]]:bg-[--amber]" />
                        </div>
                    </div>
                )}

                <CardFooter className="flex justify-end gap-3 px-6 py-4">
                    <Button
                        type="button"
                        variant="secondary"
                        onClick={() => window.history.back()}
                        disabled={processing}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        disabled={processing || isProcessingFile || (mode === 'create' && !data.audio_file)}
                    >
                        {processing && uploadProgress === 0 && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {processing ? 'Uploading...' : mode === 'create' ? 'Upload' : 'Save changes'}
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
}
