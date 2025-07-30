import React, { useRef, useState, ChangeEvent, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Loader2, Upload, File as FileIcon, Music } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import InputError from '@/components/input-error';
import { type Upload as UploadType } from '@/types';

export interface UploadFormData {
    title: string;
    description: string;
    audio_file: File | null;
    _method?: 'PUT';
}

interface MusicLibraryUploadFormProps {
    mode: 'create' | 'edit';
    data: UploadFormData;
    setData: (key: keyof UploadFormData | string, value: any) => void;
    errors: Partial<Record<keyof UploadFormData, string>>;
    processing: boolean;
    onSubmit: (e: React.FormEvent) => void;
    upload?: UploadType;
    uploadProgress?: number;
    wasSuccessful?: boolean;
    onReset?: () => void;
}

interface FileMetadata {
    name: string;
    size: string;
    type: string;
    duration: string;
}

const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

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
    onReset
}: MusicLibraryUploadFormProps) {
    const [fileMetadata, setFileMetadata] = useState<FileMetadata | null>(null);
    const [isProcessingFile, setIsProcessingFile] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (wasSuccessful && onReset) {
            setFileMetadata(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    }, [wasSuccessful, onReset]);

    useEffect(() => {
        if (mode === 'edit' && upload) {
            if (upload.filename && upload.size && upload.mime_type) {
                setFileMetadata({
                    name: upload.filename,
                    size: formatFileSize(upload.size),
                    type: upload.mime_type,
                    duration: formatDuration(upload.duration || 0),
                });
            }
        }
    }, [mode, upload]);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsProcessingFile(true);
        setData('audio_file', file);

        const audio = document.createElement('audio');
        audio.src = URL.createObjectURL(file);
        audio.onloadedmetadata = () => {
            setFileMetadata({
                name: file.name,
                size: formatFileSize(file.size),
                type: file.type,
                duration: formatDuration(audio.duration),
            });
            setIsProcessingFile(false);
            if (!data.title) {
                setData('title', file.name.replace(/\.[^/.]+$/, ''));
            }
        };
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
                            className={`flex flex-col items-center justify-center w-full p-6 border-2 border-dashed rounded-lg cursor-pointer bg-card hover:bg-muted/50 ${errors.audio_file ? 'border-destructive' : ''}`}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <Upload className="w-10 h-10 mb-3 text-muted-foreground" />
                            <p className="mb-2 text-sm text-muted-foreground">
                                <span className="font-semibold">Click to upload</span> or drag and drop
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
                            <div className="p-4 border rounded-lg bg-muted/50">
                                {isProcessingFile ? (
                                    <div className="flex items-center text-sm text-muted-foreground">
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Processing file...
                                    </div>
                                ) : fileMetadata && (
                                    <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                        <div className="flex items-center col-span-2 space-x-2 font-medium">
                                            <Music className="w-4 h-4" />
                                            <span className="truncate">{fileMetadata.name}</span>
                                        </div>
                                        <div><strong className="font-semibold">Size:</strong> {fileMetadata.size}</div>
                                        <div><strong className="font-semibold">Duration:</strong> {fileMetadata.duration}</div>
                                        <div className="col-span-2"><strong className="font-semibold">Type:</strong> {fileMetadata.type}</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="title">Title <span className="text-destructive">*</span></Label>
                        <Input
                            id="title"
                            type="text"
                            value={data.title}
                            onChange={(e) => setData('title', e.target.value)}
                            disabled={processing}
                        />
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
                            <div className="flex justify-between text-sm">
                                <span>Uploading...</span>
                                <span>{uploadProgress}%</span>
                            </div>
                            <Progress value={uploadProgress} className="h-2" />
                        </div>
                    </div>
                )}
                <CardFooter className="flex justify-end space-x-2">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => window.history.back()}
                        disabled={processing}
                    >
                        Cancel
                    </Button>
                    <Button type="submit" disabled={processing || isProcessingFile || (mode === 'create' && !data.audio_file)}>
                        {processing && uploadProgress === 0 && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                        {processing ? 'Uploading...' : (mode === 'create' ? 'Upload' : 'Save Changes')}
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
}
