import { Head, useForm } from '@inertiajs/react';
import AppLayout from '@/layouts/app-layout';
import { MusicLibraryUploadForm } from '@/components/music-library-upload-form';
import { type BreadcrumbItem, type Upload as UploadType } from '@/types';

interface EditUploadProps {
    upload: UploadType;
}

export default function Edit({ upload }: EditUploadProps) {
    // Ensure upload has the expected properties before initializing the form
    if (!upload || typeof upload !== 'object') {
        return <div>Loading upload data...</div>;
    }

    // Extract the actual upload data - it might be nested inside a data property
    const uploadData = 'data' in upload && upload.data ? upload.data as UploadType : upload;

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
    const setFormData = (key: string, value: any) => {
        form.setData(key as any, value);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        
        form.post(route('uploads.update', { upload: uploadData.id }), {
            forceFormData: true,
            preserveScroll: true,
            onSuccess: () => {
                if (form.data.audio_file) {
                    form.reset('audio_file');
                }
            },
        });
    };

    const breadcrumbs: BreadcrumbItem[] = [
        { title: 'Music Library', href: route('uploads.index') },
        // { title: upload.title, href: route('uploads.show', { upload: upload.id }), description: 'View track details' },
        // { title: 'Edit', href: route('uploads.edit', { upload: upload.id }), description: 'Edit this track' },
    ];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={`Edit ${uploadData.title}`} />
            <div className="max-w-2xl mx-auto py-8">
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
