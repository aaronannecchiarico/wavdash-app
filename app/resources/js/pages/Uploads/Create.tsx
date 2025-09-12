import { MusicLibraryUploadForm } from '@/components/music-library-upload-form';
import AppLayout from '@/layouts/app-layout';
import { generateDynamicBreadcrumbs } from '@/lib/breadcrumb-utils';
import { type BreadcrumbItem } from '@/types';
import { Head, useForm } from '@inertiajs/react';
import { useState } from 'react';

interface AudioProcessingConfig {
    client_side_processing_enabled: boolean;
    ab_test_enabled: boolean;
    should_use_client_processing: boolean;
    fallback_on_error: boolean;
    monitor_performance: boolean;
}

interface CreateProps {
    audioProcessingConfig: AudioProcessingConfig;
}

export default function Create({ audioProcessingConfig }: CreateProps) {
    const { data, setData, post, errors, processing, reset, wasSuccessful } = useForm({
        title: '',
        description: '',
        audio_file: null as File | null,
        client_processed: false,
        original_filename: '',
        original_size: 0,
        duration: 0,
        processing_time_ms: 0,
    });

    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [processedFileData, setProcessedFileData] = useState<{
        processedFile: File;
        originalFilename: string;
        originalSize: number;
        duration: number;
        processingTimeMs: number;
    } | null>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        
        // Update the form data with client processing metadata if available
        if (processedFileData) {
            setData({
                ...data,
                client_processed: true,
                original_filename: processedFileData.originalFilename,
                original_size: processedFileData.originalSize,
                duration: processedFileData.duration,
                processing_time_ms: processedFileData.processingTimeMs,
            });
        }
        
        post(route('uploads.store'), {
            forceFormData: true,
            preserveScroll: true,
            onProgress: (progress) => {
                if (progress && typeof progress.percentage === 'number') {
                    setUploadProgress(progress.percentage);
                }
            },
            onSuccess: () => {
                reset();
                setProcessedFileData(null);
            },
            onFinish: () => {
                setUploadProgress(0);
            },
        });
    };

    const breadcrumbs: BreadcrumbItem[] = generateDynamicBreadcrumbs('Upload', route('uploads.create'), 'Add a new track to your library');

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Upload Audio" />
            <div className="mx-auto max-w-4xl py-8">
                <MusicLibraryUploadForm
                    mode="create"
                    data={data}
                    setData={setData}
                    errors={errors}
                    processing={processing}
                    onSubmit={handleSubmit}
                    uploadProgress={uploadProgress}
                    wasSuccessful={wasSuccessful}
                    onReset={() => reset()}
                    onProcessedFile={setProcessedFileData}
                    audioProcessingConfig={audioProcessingConfig}
                />
            </div>
        </AppLayout>
    );
}
