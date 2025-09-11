import { MusicLibraryUploadForm } from '@/components/music-library-upload-form';
import AppLayout from '@/layouts/app-layout';
import { generateDynamicBreadcrumbs } from '@/lib/breadcrumb-utils';
import { type BreadcrumbItem, type Upload as UploadType } from '@/types';
import { Head, useForm } from '@inertiajs/react';

interface EditUploadProps {
    upload: UploadType;
}

export default function Edit({ upload }: EditUploadProps) {
    // Extract the actual upload data - it might be nested inside a data property
    const uploadData = 'data' in upload && upload.data ? (upload.data as UploadType) : upload;

    // Initialize the form with the upload data
    const form = useForm<{
        title: string;
        description: string;
        audio_file: File | null;
        _method: 'PUT';
    }>({
        title: uploadData?.title || '',
        description: uploadData?.description || '',
        audio_file: null,
        _method: 'PUT',
    });

    // Adapter function to match the expected signature in MusicLibraryUploadForm
    const setFormData = (key: string, value: unknown) => {
        // Type guard to ensure value is compatible with expected form data types
        if ((key === 'audio_file' && value instanceof File) || value === null) {
            form.setData(key as 'audio_file', value as File | null);
        } else if (typeof value === 'string' && (key === 'title' || key === 'description' || key === '_method')) {
            form.setData(key, value);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        form.post(route('uploads.update', uploadData.id), {
            forceFormData: true,
            preserveScroll: true,
            onSuccess: () => {
                if (form.data.audio_file) {
                    form.reset('audio_file');
                }
            },
        });
    };

    const breadcrumbs: BreadcrumbItem[] = (() => {
        const baseBreadcrumbs = generateDynamicBreadcrumbs('Edit', route('uploads.edit', uploadData.id), 'Edit this track');

        // Insert the track title between parent and current page
        return [
            baseBreadcrumbs[0], // Parent (Dashboard or Music Library)
            { title: uploadData.title, href: route('uploads.show', uploadData.id), description: 'View track details' },
            baseBreadcrumbs[1], // Current page (Edit)
        ];
    })();

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Edit ${uploadData.title}`} />
            <div className="mx-auto max-w-2xl py-8">
                <MusicLibraryUploadForm
                    mode="edit"
                    data={form.data}
                    setData={setFormData}
                    errors={form.errors}
                    processing={form.processing}
                    onSubmit={handleSubmit}
                    upload={uploadData}
                    wasSuccessful={form.wasSuccessful}
                    onReset={() => form.reset('audio_file')}
                />
            </div>
        </AppLayout>
    );
}
