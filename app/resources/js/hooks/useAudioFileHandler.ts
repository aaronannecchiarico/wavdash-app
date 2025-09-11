import { formatDuration, formatFileSize } from '@/lib/formatters';
import { ChangeEvent, useEffect, useRef, useState } from 'react';

interface FileMetadata {
    name: string;
    size: string;
    type: string;
    duration: string;
}

interface UseAudioFileHandlerProps {
    initialTitle?: string;
    onTitleSuggestion?: (title: string) => void;
}

interface UseAudioFileHandlerReturn {
    fileMetadata: FileMetadata | null;
    isProcessingFile: boolean;
    fileInputRef: React.RefObject<HTMLInputElement | null>;
    handleFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
    objectUrl: string | null;
    resetFileInput: () => void;
}

export const useAudioFileHandler = ({ initialTitle = '', onTitleSuggestion }: UseAudioFileHandlerProps = {}): UseAudioFileHandlerReturn => {
    const [fileMetadata, setFileMetadata] = useState<FileMetadata | null>(null);
    const [isProcessingFile, setIsProcessingFile] = useState(false);
    const [objectUrl, setObjectUrl] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Clean up object URL when component unmounts or when a new URL is created
    useEffect(() => {
        return () => {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
        };
    }, [objectUrl]);

    const resetFileInput = () => {
        setFileMetadata(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
        if (objectUrl) {
            URL.revokeObjectURL(objectUrl);
            setObjectUrl(null);
        }
    };

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsProcessingFile(true);

        // Clean up previous objectURL if exists
        if (objectUrl) {
            URL.revokeObjectURL(objectUrl);
        }

        // Create new objectURL
        const newObjectUrl = URL.createObjectURL(file);
        setObjectUrl(newObjectUrl);

        const audio = document.createElement('audio');
        audio.src = newObjectUrl;

        audio.onloadedmetadata = () => {
            setFileMetadata({
                name: file.name,
                size: formatFileSize(file.size),
                type: file.type,
                duration: formatDuration(audio.duration),
            });
            setIsProcessingFile(false);

            // Suggest filename as title if callback is provided
            if (onTitleSuggestion && !initialTitle) {
                const suggestedTitle = file.name.replace(/\.[^/.]+$/, '');
                onTitleSuggestion(suggestedTitle);
            }
        };

        audio.onerror = () => {
            setIsProcessingFile(false);
            // Could add error handling here
            console.error('Error loading audio file metadata');
        };
    };

    return {
        fileMetadata,
        isProcessingFile,
        fileInputRef,
        handleFileChange,
        objectUrl,
        resetFileInput,
    };
};
