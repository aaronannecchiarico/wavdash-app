import { LucideIcon } from 'lucide-react';
import type { Config } from 'ziggy-js';

export interface Auth {
    user: User;
}

export interface BreadcrumbItem {
    title: string;
    href: string;
    description?: string;
}

export interface NavGroup {
    title: string;
    items: NavItem[];
}

export interface NavItem {
    title: string;
    href: string;
    icon?: LucideIcon | null;
    isActive?: boolean;
}

export interface SharedData {
    name: string;
    quote: { message: string; author: string };
    auth: Auth;
    ziggy: Config & { location: string };
    sidebarOpen: boolean;
    [key: string]: unknown;
}

export interface PaginatedData<T> {
    data: T[];
    links: {
        first: string;
        last: string;
        prev: string | null;
        next: string | null;
    };
    meta: {
        total: number;
        to: number;
        current_page: number;
        from: number;
        last_page: number;
        links: {
            url: string | null;
            label: string;
            active: boolean;
        }[];
    };
}

export interface User {
    id: number;
    name: string;
    email: string;
    avatar?: string;
    email_verified_at: string | null;
    created_at: string;
    updated_at: string;
    [key: string]: unknown; // This allows for additional properties...
}

export interface UploadAnalysisTask {
    id: number;
    task_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'deleted';
    progress: number;
    submitted_at: string;
    completed_at: string | null;
    error_message: string | null;
}

export interface UploadAnalysis {
    id: number;
    musical_key: string | null;
    key_confidence: number | null;
    bpm: number | null;
    beat_regularity: number | null;
    loudness_db: number | null;
    dynamic_range_db: number | null;
    brightness: number | null;
    timbral_complexity: number | null;
    analysis_duration: number | null;
    chunk_count: number | null;
    key_changes: number | null;
    created_at: string;
    categories?: {
        bpm: string | null;
        loudness: string | null;
        dynamic_range: string | null;
        brightness: string | null;
    };
    reliability?: {
        has_reliable_key: boolean;
        is_atonal_complex: boolean;
    };
}

export interface UploadStemTask {
    id: number;
    task_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'deleted';
    progress: number;
    submitted_at: string;
    completed_at: string | null;
    error_message: string | null;
}

export interface StemMetadata {
    quality_score?: number;
    processing_time?: number;
    algorithm_version?: string;
    separation_confidence?: number;
    [key: string]: unknown;
}

export interface UploadStem {
    id: number;
    stem_type: string;
    file_path: string;
    storage_type: string;
    file_size?: number;
    duration?: number;
    metadata?: StemMetadata;
    created_at: string;
    updated_at: string;
    formatted_file_size?: string;
    formatted_duration?: string;
    stem_type_name?: string;
}

export interface TempoProcessingOptions {
    preset?: string;
    tempo_factor?: number;
    pitch_shift_semitones?: number;
    preserve_pitch?: boolean;
    add_reverb?: boolean;
    use_stems?: boolean;
    [key: string]: unknown;
}

export interface UploadTempoTask {
    id: number;
    task_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'deleted';
    progress: number;
    processing_options?: TempoProcessingOptions;
    submitted_at: string;
    completed_at: string | null;
    error_message: string | null;
}

export interface TempoProcessingMetadata {
    quality_score?: number;
    processing_warnings?: string[];
    processing_time?: number;
    algorithm_version?: string;
    [key: string]: unknown;
}

export interface UploadTempo {
    id: number;
    preset: string;
    tempo_factor: number;
    pitch_shift_semitones?: number;
    preserve_pitch: boolean;
    add_reverb: boolean;
    use_stems: boolean;
    file_path: string;
    storage_type: string;
    file_size?: number;
    duration?: number;
    final_bpm?: number;
    processing_metadata?: TempoProcessingMetadata;
    created_at: string;
    updated_at: string;
    preset_name?: string;
    formatted_file_size?: string;
    formatted_duration?: string;
    tempo_description?: string;
    pitch_description?: string;
    public_path?: string; // Adding this property since it was used in the tempo component
}

export interface Upload {
    id: number;
    title: string;
    description: string | null;
    filename: string;
    mime_type: string;
    size: number;
    status: string;
    duration?: number;
    stream_url: string | null;
    created_at: string;
    updated_at: string;
    user: User;
    artist?: string;
    genre?: string;
    bitrate?: number;
    // Analysis-related properties
    analysis_task?: UploadAnalysisTask | null;
    analysis?: UploadAnalysis | null;
    has_analysis?: boolean;
    is_analysis_in_progress?: boolean;
    // Stem separation properties
    stem_task?: UploadStemTask | null;
    stems?: UploadStem[];
    has_stems?: boolean;
    is_stem_separation_in_progress?: boolean;
    // Tempo processing properties
    tempo_task?: UploadTempoTask | null;
    tempos?: UploadTempo[];
    has_tempos?: boolean;
    is_tempo_processing_in_progress?: boolean;
}
