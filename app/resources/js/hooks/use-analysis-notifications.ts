import { useEcho } from '@/components/echo-provider';
import { router, usePage } from '@inertiajs/react';
import { useEffect } from 'react';
import { toast } from 'sonner';

interface AnalysisCompletedEvent {
    upload_id: number;
    task_id: string;
    status: 'completed' | 'failed';
    has_analysis: boolean;
    error_message?: string;
    analysis_url: string;
}

export function useAnalysisNotifications() {
    const { auth } = usePage().props as any;
    const { echo } = useEcho();

    useEffect(() => {
        if (auth.user && echo) {
            const channel = echo.private(`App.Models.User.${auth.user.id}`);

            const listener = (e: AnalysisCompletedEvent) => {
                console.log('Analysis completion event received:', e);
                
                if (e.status === 'completed' && e.has_analysis) {
                    toast.success('Analysis completed successfully!', {
                        description: 'Your audio analysis is now ready to view.',
                        action: {
                            label: 'View Results',
                            onClick: () => router.visit(e.analysis_url),
                        },
                    });
                } else if (e.status === 'failed') {
                    toast.error('Analysis failed', {
                        description: e.error_message || 'There was an issue analyzing your audio. Please try again.',
                        action: {
                            label: 'Try Again',
                            onClick: () => router.visit(e.analysis_url),
                        },
                    });
                } else if (e.status === 'completed' && !e.has_analysis) {
                    toast.warning('Analysis completed with issues', {
                        description: 'The analysis finished but no results were found.',
                        action: {
                            label: 'View Details',
                            onClick: () => router.visit(e.analysis_url),
                        },
                    });
                }

                // Refresh the current page if user is viewing the analysis page
                const currentUrl = window.location.pathname;
                if (currentUrl.includes(`/uploads/${e.upload_id}/analysis`)) {
                    router.reload({ only: ['upload'] });
                }
            };

            channel.listen('.analysis.completed', listener);

            return () => {
                channel.stopListening('.analysis.completed', listener);
            };
        }
    }, [auth.user, echo]);
}