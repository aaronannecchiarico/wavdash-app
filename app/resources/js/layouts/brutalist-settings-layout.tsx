import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { type NavItem } from '@/types';
import { Link } from '@inertiajs/react';
import { Lock, Palette, Settings, User } from 'lucide-react';
import { type PropsWithChildren } from 'react';

const sidebarNavItems: NavItem[] = [
    {
        title: 'PROFILE',
        href: '/settings/profile',
        icon: User,
    },
    {
        title: 'PASSWORD',
        href: '/settings/password',
        icon: Lock,
    },
    {
        title: 'APPEARANCE',
        href: '/settings/appearance',
        icon: Palette,
    },
];

export default function BrutalistSettingsLayout({ children }: PropsWithChildren) {
    // When server-side rendering, we only render the layout on the client...
    if (typeof window === 'undefined') {
        return null;
    }

    const currentPath = window.location.pathname;

    return (
        <div className="min-h-screen bg-background px-6 py-8">
            {/* Header */}
            <div className="mb-8">
                <div className="mb-4 flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center border-2 border-border bg-chart-4 shadow-shadow">
                        <Settings className="h-6 w-6 text-main-foreground" />
                    </div>
                    <div>
                        <h1 className="font-heading text-3xl font-black tracking-widest text-foreground uppercase">SETTINGS</h1>
                        <p className="text-sm font-base font-bold tracking-wide text-foreground/70 uppercase">CONFIGURE YOUR FORGE EXPERIENCE</p>
                    </div>
                </div>
                <div className="h-1 w-full bg-border"></div>
            </div>

            <div className="flex flex-col gap-8 lg:flex-row">
                {/* Navigation Sidebar */}
                <aside className="w-full flex-shrink-0 lg:w-64">
                    <div className="border-2 border-border bg-background p-4 shadow-shadow">
                        <h2 className="mb-4 font-heading text-sm font-black tracking-widest text-foreground uppercase">NAVIGATION</h2>
                        <nav className="space-y-2">
                            {sidebarNavItems.map((item, index) => {
                                const Icon = item.icon;
                                const isActive = currentPath === item.href;

                                return (
                                    <Button
                                        key={`${item.href}-${index}`}
                                        variant="secondary"
                                        asChild
                                        className={cn(
                                            'h-12 w-full justify-start border-2 transition-all',
                                            'font-heading text-sm font-black tracking-wide uppercase',
                                            isActive
                                                ? 'border-border bg-chart-1 text-main-foreground shadow-shadow'
                                                : 'border-border bg-background text-foreground hover:bg-chart-1 hover:text-main-foreground hover:shadow-shadow',
                                        )}
                                    >
                                        <Link href={item.href} prefetch>
                                            {Icon && <Icon className="mr-3 h-4 w-4" />}
                                            {item.title}
                                        </Link>
                                    </Button>
                                );
                            })}
                        </nav>
                    </div>
                </aside>

                {/* Main Content */}
                <div className="flex-1">
                    <div className="border-2 border-border bg-background p-6 shadow-shadow">{children}</div>
                </div>
            </div>
        </div>
    );
}
