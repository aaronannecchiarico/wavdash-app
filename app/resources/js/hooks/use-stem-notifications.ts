import { useEcho } from '@/components/echo-provider';
import type { SharedData } from '@/types';
import { router, usePage } from '@inertiajs/react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface StemSeparationCompletedEvent {
    upload_id: number;
    task_id: string;
    status: 'completed' | 'failed';
    has_stems: boolean;
    error_message?: string;
    stems_url: string;
}

export function useStemNotifications() {
    const { auth } = usePage<SharedData>().props;
    const { echo } = useEcho();

    useEffect(() => {
        if (auth.user && echo) {
            const channel = echo.private(`App.Models.User.${auth.user.id}`);

            const listener = (e: StemSeparationCompletedEvent) => {
                console.log('Stem separation completion event received:', e);

                if (e.status === 'completed' && e.has_stems) {
                    toast.success('Stem separation completed successfully!', {
                        description: 'Your stems are now ready to download and play.',
                        action: {
                            label: 'View Stems',
                            onClick: () => router.visit(e.stems_url),
                        },
                    });
                } else if (e.status === 'failed') {
                    toast.error('Stem separation failed', {
                        description: e.error_message || 'There was an issue separating your audio. Please try again.',
                        action: {
                            label: 'Try Again',
                            onClick: () => router.visit(e.stems_url),
                        },
                    });
                } else if (e.status === 'completed' && !e.has_stems) {
                    toast.warning('Stem separation completed with issues', {
                        description: 'The separation finished but no stems were found.',
                        action: {
                            label: 'View Details',
                            onClick: () => router.visit(e.stems_url),
                        },
                    });
                }

                // Refresh the current page if user is viewing the stems page
                const currentUrl = window.location.pathname;
                if (currentUrl.includes(`/uploads/${e.upload_id}/stems`)) {
                    router.reload({ only: ['upload'] });
                }
            };

            channel.listen('.stem-separation.completed', listener);

            return () => {
                channel.stopListening('.stem-separation.completed', listener);
            };
        }
    }, [auth.user, echo]);
}
