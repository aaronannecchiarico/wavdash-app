import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import { formatDistance } from 'date-fns';
import { PencilIcon, Trash2Icon as TrashIcon } from 'lucide-react';

interface Upload {
    id: number;
    title: string;
    description: string | null;
    filename: string;
    mime_type: string;
    size: number;
    status: string;
    stream_url: string | null;
    created_at: string;
    updated_at: string;
    user: {
        id: number;
        name: string;
    };
}

interface Props {
    upload: Upload;
}

export default function Show({ upload }: Props) {
    // Format file size to human-readable format
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // Get status badge color based on status
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'ready':
                return 'bg-green-100 text-green-800';
            case 'processing':
                return 'bg-blue-100 text-blue-800';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const breadcrumbs: BreadcrumbItem[] = [
        { title: 'Music Library', href: route('uploads.index') },
        { title: upload.title, href: route('uploads.show', { upload: upload.id }), description: 'View track details' },
    ];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={upload.title} />

            <div className="mx-auto max-w-4xl py-8">
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>{upload.title}</CardTitle>
                                <CardDescription>
                                    Uploaded {formatDistance(new Date(upload.created_at), new Date(), { addSuffix: true })}
                                </CardDescription>
                            </div>
                            <span className={`inline-block rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(upload.status)}`}>
                                {upload.status.charAt(0).toUpperCase() + upload.status.slice(1)}
                            </span>
                        </div>
                    </CardHeader>

                    <CardContent className="space-y-6">
                        {upload.description && (
                            <div>
                                <h3 className="mb-2 text-sm font-medium text-gray-700">Description</h3>
                                <p className="text-gray-600">{upload.description}</p>
                            </div>
                        )}

                        <div>
                            <h3 className="mb-2 text-sm font-medium text-gray-700">File Details</h3>
                            <dl className="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Filename</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{upload.filename}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Type</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{upload.mime_type}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Size</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{formatFileSize(upload.size)}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                                    <dd className="mt-1 text-sm text-gray-900">
                                        {formatDistance(new Date(upload.updated_at), new Date(), { addSuffix: true })}
                                    </dd>
                                </div>
                            </dl>
                        </div>

                        {upload.status === 'ready' && upload.stream_url && (
                            <div>
                                <h3 className="mb-2 text-sm font-medium text-gray-700">Preview</h3>
                                <audio controls className="w-full">
                                    <source src={upload.stream_url} type={upload.mime_type} />
                                    Your browser does not support the audio element.
                                </audio>
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="flex justify-between bg-gray-50">
                        <Link href={route('uploads.edit', { upload: upload.id })}>
                            <Button variant="outline">
                                <PencilIcon className="mr-2 h-4 w-4" />
                                Edit
                            </Button>
                        </Link>

                        <Link
                            href={route('uploads.destroy', { upload: upload.id })}
                            method="delete"
                            as="button"
                            type="button"
                            className="inline-flex items-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-xs font-semibold tracking-widest text-white uppercase hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none"
                        >
                            <TrashIcon className="mr-2 h-4 w-4" />
                            Delete
                        </Link>
                    </CardFooter>
                </Card>
            </div>
        </AppLayout>
    );
}
