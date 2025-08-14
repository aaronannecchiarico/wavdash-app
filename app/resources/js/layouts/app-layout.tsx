import { EchoProvider } from '@/components/echo-provider';
import { Toaster } from '@/components/ui/sonner';
import AppLayoutTemplate from '@/layouts/app/app-sidebar-layout';
import { useUploadNotifications } from '@/hooks/use-upload-notifications';
import { useAnalysisNotifications } from '@/hooks/use-analysis-notifications';
import { type BreadcrumbItem } from '@/types';
import { type ReactNode } from 'react';

interface AppLayoutProps {
    children: ReactNode;
    breadcrumbs?: BreadcrumbItem[];
}

const NotificationHandler = () => {
    useUploadNotifications();
    useAnalysisNotifications();
    return null;
};

export default ({ children, breadcrumbs, ...props }: AppLayoutProps) => (
    <EchoProvider>
        <AppLayoutTemplate breadcrumbs={breadcrumbs} {...props}>
            {children}
            <NotificationHandler />
        </AppLayoutTemplate>
    </EchoProvider>
);
