import { useEcho } from '@/components/echo-provider';
import { router, usePage } from '@inertiajs/react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface UploadProcessedEvent {
    id: number;
    title: string;
    status: 'ready' | 'failed';
    url: string;
}

export function useUploadNotifications() {
    const { auth } = usePage().props as any;
    const { echo } = useEcho();

    useEffect(() => {
        if (auth.user && echo) {
            const channel = echo.private(`App.Models.User.${auth.user.id}`);

            const listener = (e: UploadProcessedEvent) => {
                if (e.status === 'ready') {
                    toast.success(`"${e.title}" is now ready!`, {
                        description: 'Your track has been processed and is available in your library.',
                        action: {
                            label: 'View',
                            onClick: () => router.visit(route('uploads.show', e.id)),
                        },
                    });
                } else if (e.status === 'failed') {
                    toast.error(`"${e.title}" failed to process.`, {
                        description: 'There was an issue processing your track. Please try uploading it again.',
                    });
                }
            };

            channel.listen('.upload.processed', listener);

            return () => {
                channel.stopListening('.upload.processed', listener);
            };
        }
    }, [auth.user, echo]);
}
