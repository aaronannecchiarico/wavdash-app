import { EchoProvider } from '@/components/echo-provider';
import { useAnalysisNotifications } from '@/hooks/use-analysis-notifications';
import { useStemNotifications } from '@/hooks/use-stem-notifications';
import { useTempoNotifications } from '@/hooks/use-tempo-notifications';
import { useUploadNotifications } from '@/hooks/use-upload-notifications';
import AppLayoutTemplate from '@/layouts/app/app-sidebar-layout';
import { type BreadcrumbItem } from '@/types';
import { type ReactNode } from 'react';

interface AppLayoutProps {
    children: ReactNode;
    breadcrumbs?: BreadcrumbItem[];
}

const NotificationHandler = () => {
    useUploadNotifications();
    useAnalysisNotifications();
    useStemNotifications();
    useTempoNotifications();
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
