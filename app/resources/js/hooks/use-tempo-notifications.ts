import { useEcho } from '@/components/echo-provider';
import type { SharedData } from '@/types';
import { router, usePage } from '@inertiajs/react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface TempoProcessingCompletedEvent {
    upload_id: number;
    task_id: string;
    status: 'completed' | 'failed';
    has_tempos: boolean;
    error_message?: string;
    tempo_url: string;
    processing_options?: { preset?: string };
}

export function useTempoNotifications() {
    const { auth } = usePage<SharedData>().props;
    const { echo } = useEcho();

    useEffect(() => {
        if (auth.user && echo) {
            const channel = echo.private(`App.Models.User.${auth.user.id}`);

            const listener = (e: TempoProcessingCompletedEvent) => {
                console.log('Tempo processing completion event received:', e);

                if (e.status === 'completed' && e.has_tempos) {
                    const presetName = e.processing_options?.preset
                        ? e.processing_options.preset.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
                        : 'Custom';

                    toast.success('Tempo processing completed successfully!', {
                        description: `Your ${presetName} tempo effect is now ready to play and download.`,
                        action: {
                            label: 'View Results',
                            onClick: () => router.visit(e.tempo_url),
                        },
                    });
                } else if (e.status === 'failed') {
                    toast.error('Tempo processing failed', {
                        description: e.error_message || 'There was an issue processing your audio tempo. Please try again.',
                        action: {
                            label: 'Try Again',
                            onClick: () => router.visit(e.tempo_url),
                        },
                    });
                } else if (e.status === 'completed' && !e.has_tempos) {
                    toast.warning('Tempo processing completed with issues', {
                        description: 'The processing finished but no tempo files were generated.',
                        action: {
                            label: 'View Details',
                            onClick: () => router.visit(e.tempo_url),
                        },
                    });
                }

                // Refresh the current page if user is viewing the tempo page
                const currentUrl = window.location.pathname;
                if (currentUrl.includes(`/uploads/${e.upload_id}/tempo`)) {
                    router.reload({ only: ['upload'] });
                }
            };

            channel.listen('.tempo.completed', listener);

            return () => {
                channel.stopListening('.tempo.completed', listener);
            };
        }
    }, [auth.user, echo]);
}
