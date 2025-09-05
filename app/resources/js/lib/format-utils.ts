/**
 * Utility functions for formatting data in the UI
 */

/**
 * Format file size from bytes to human readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Format duration from seconds to MM:SS format
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '--:--';
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * Format bitrate with units
 */
export function formatBitrate(bitrate: number): string {
  if (!bitrate) return 'Unknown';
  
  if (bitrate >= 1000) {
    return `${Math.round(bitrate / 1000)} Mbps`;
  }
  
  return `${bitrate} kbps`;
}

/**
 * Get audio format from mime type
 */
export function getAudioFormat(mimeType: string): string {
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
    'audio/x-m4a': 'M4A'
  };
  
  return formats[mimeType] || mimeType.split('/').pop()?.toUpperCase() || 'UNKNOWN';
}

/**
 * Get processing progress percentage
 */
export function getProcessingProgress(upload: any): { type: string; progress: number } | null {
  if (upload.is_analysis_in_progress) {
    return { type: 'analysis', progress: 65 }; // Could be enhanced with actual progress data
  }
  
  if (upload.is_stem_separation_in_progress) {
    return { type: 'stems', progress: 45 };
  }
  
  if (upload.is_tempo_processing_in_progress) {
    return { type: 'tempo', progress: 30 };
  }
  
  return null;
}