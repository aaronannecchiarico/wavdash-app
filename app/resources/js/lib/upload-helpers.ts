export const getAudioFormat = (mimeType: string): string => {
    const formats: { [key: string]: string } = {
        'audio/mpeg': 'MP3',
        'audio/wav': 'WAV',
        'audio/flac': 'FLAC',
        'audio/aac': 'AAC',
        'audio/ogg': 'OGG',
        'audio/m4a': 'M4A',
        'audio/wma': 'WMA',
    };
    return formats[mimeType] || 'AUDIO';
};

export const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
        case 'completed':
        case 'success':
        case 'ready':
            return 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 dark:hover:bg-green-900/40';
        case 'processing':
        case 'pending':
            return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300 dark:hover:bg-yellow-900/40';
        case 'failed':
        case 'error':
            return 'bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/40';
        default:
            return 'bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700';
    }
};
