export const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

export const formatDuration = (seconds: number): string => {
    if (!seconds || seconds < 0) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
};

// Audio format extraction from mime type
export const getAudioFormat = (mimeType: string): string => {
    const formats: Record<string, string> = {
        'audio/mpeg': 'MP3',
        'audio/mp3': 'MP3',
        'audio/wav': 'WAV',
        'audio/x-wav': 'WAV',
        'audio/wave': 'WAV',
        'audio/flac': 'FLAC',
        'audio/x-flac': 'FLAC',
        'audio/aac': 'AAC',
        'audio/ogg': 'OGG',
        'audio/mp4': 'M4A',
        'audio/x-m4a': 'M4A',
        'audio/wma': 'WMA',
    };
    return formats[mimeType] || mimeType.split('/').pop()?.toUpperCase() || 'UNKNOWN';
};

// Format bitrate with proper units
export const formatBitrate = (bitrate: number): string => {
    if (!bitrate) return 'Unknown';
    if (bitrate >= 1000) {
        return `${Math.round(bitrate / 1000)} Mbps`;
    }
    return `${bitrate} kbps`;
};
