import InputError from '@/components/input-error';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
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
                        <CardTitle>{mode === 'create' ? 'Upload Audio' : 'Edit Audio'}</CardTitle>
                    <CardDescription>
                        {mode === 'create' ? 'Upload an audio file to use in beats and contests.' : 'Update the details for this audio file.'}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="audio_file">Audio File {mode === 'create' && <span className="text-destructive">*</span>}</Label>
                        <div
                            className={`flex w-full cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed bg-card p-6 hover:bg-muted/50 dark:hover:bg-slate-800/70 transition-colors duration-200 ${errors.audio_file ? 'border-destructive' : 'dark:border-slate-700'}`}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <Upload className="mb-3 h-10 w-10 text-muted-foreground dark:text-slate-400" />
                            <p className="mb-2 text-sm text-muted-foreground">
                                <span className="font-semibold dark:text-slate-300">Click to upload</span> or drag and drop
                            </p>
                            <p className="text-xs text-muted-foreground">MP3, WAV, AIFF or FLAC (max. 50MB)</p>
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
                            <Label>File Details</Label>
                            <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-muted/50 dark:bg-slate-900/40 p-4">
                                {isProcessingFile ? (
                                    <div className="flex items-center text-sm text-muted-foreground">
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Processing file...
                                    </div>
                                ) : (
                                    fileMetadata && (
                                        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                            <div className="col-span-2 flex items-center space-x-2 font-medium">
                                                <Music className="h-4 w-4 text-blue-500 dark:text-blue-400" />
                                                <span className="truncate">{fileMetadata.name}</span>
                                            </div>
                                            <div>
                                                <strong className="font-semibold">Size:</strong>{' '}
                                                <span className="text-muted-foreground">{fileMetadata.size}</span>
                                            </div>
                                            <div>
                                                <strong className="font-semibold">Duration:</strong>{' '}
                                                <span className="text-muted-foreground">{fileMetadata.duration}</span>
                                            </div>
                                            <div className="col-span-2">
                                                <strong className="font-semibold">Type:</strong>{' '}
                                                <span className="text-muted-foreground">{fileMetadata.type}</span>
                                            </div>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="title">
                            Title <span className="text-destructive">*</span>
                        </Label>
                        <Input id="title" type="text" value={data.title} onChange={(e) => setData('title', e.target.value)} disabled={processing} />
                        <InputError message={errors.title} />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="description">Description (optional)</Label>
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
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm text-muted-foreground">
                                <span className="flex items-center">
                                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                    Uploading...
                                </span>
                                <span className="font-medium text-foreground">{uploadProgress}%</span>
                            </div>
                            <Progress value={uploadProgress} className="h-2" />
                        </div>
                    </div>
                )}
                <CardFooter className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => window.history.back()} disabled={processing}>
                        Cancel
                    </Button>
                    <Button type="submit" disabled={processing || isProcessingFile || (mode === 'create' && !data.audio_file)}>
                        {processing && uploadProgress === 0 && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {processing ? 'Uploading...' : mode === 'create' ? 'Upload' : 'Save Changes'}
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
}
