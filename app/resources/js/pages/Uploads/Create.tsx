import { MusicLibraryUploadForm } from '@/components/music-library-upload-form';
import AppLayout from '@/layouts/app-layout';
import { generateDynamicBreadcrumbs } from '@/lib/breadcrumb-utils';
import { type BreadcrumbItem } from '@/types';
import { Head, useForm } from '@inertiajs/react';
import { useState } from 'react';

export default function Create() {
    const { data, setData, post, errors, processing, reset, wasSuccessful } = useForm({
        title: '',
        description: '',
        audio_file: null as File | null,
    });

    const [uploadProgress, setUploadProgress] = useState<number>(0);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
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
            },
            onFinish: () => {
                setUploadProgress(0);
            },
        });
    };

    const breadcrumbs: BreadcrumbItem[] = generateDynamicBreadcrumbs(
        'Upload',
        route('uploads.create'),
        'Add a new track to your library'
    );

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
                />
            </div>
        </AppLayout>
    );
}
