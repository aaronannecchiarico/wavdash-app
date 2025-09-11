import { BreadcrumbItem } from '@/types';

/**
 * Generate dynamic breadcrumbs based on the previous page
 * This helps maintain proper navigation context
 */
export function generateDynamicBreadcrumbs(currentTitle: string, currentHref: string, description?: string, previousUrl?: string): BreadcrumbItem[] {
    const breadcrumbs: BreadcrumbItem[] = [];

    // Determine the parent page based on the previous URL or current context
    if (previousUrl?.includes('/dashboard') || window.location.search.includes('from=dashboard')) {
        breadcrumbs.push({
            title: 'Dashboard',
            href: '/dashboard',
        });
    } else {
        // Default to Music Library for upload-related pages
        breadcrumbs.push({
            title: 'Music Library',
            href: '/uploads',
        });
    }

    // Add current page
    breadcrumbs.push({
        title: currentTitle,
        href: currentHref,
        description,
    });

    return breadcrumbs;
}

/**
 * Check if navigation came from dashboard
 */
export function isNavigatingFromDashboard(): boolean {
    return document.referrer?.includes('/dashboard') || window.location.search.includes('from=dashboard');
}
