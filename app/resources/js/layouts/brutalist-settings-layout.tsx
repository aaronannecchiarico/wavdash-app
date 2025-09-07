import { Button } from '@/components/ui/neo/button';
import { cn } from '@/lib/utils';
import { type NavItem } from '@/types';
import { Link } from '@inertiajs/react';
import { Settings, User, Lock, Palette } from 'lucide-react';
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
        <div className="px-6 py-8 bg-background min-h-screen">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-chart-4 border-2 border-border shadow-shadow flex items-center justify-center">
                        <Settings className="h-6 w-6 text-main-foreground" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-heading font-black uppercase tracking-widest text-foreground">
                            SETTINGS
                        </h1>
                        <p className="font-base font-bold text-foreground/70 uppercase tracking-wide text-sm">
                            CONFIGURE YOUR FORGE EXPERIENCE
                        </p>
                    </div>
                </div>
                <div className="w-full h-1 bg-border"></div>
            </div>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Navigation Sidebar */}
                <aside className="w-full lg:w-64 flex-shrink-0">
                    <div className="border-2 border-border shadow-shadow bg-background p-4">
                        <h2 className="font-heading font-black text-sm uppercase tracking-widest text-foreground mb-4">
                            NAVIGATION
                        </h2>
                        <nav className="space-y-2">
                            {sidebarNavItems.map((item, index) => {
                                const Icon = item.icon;
                                const isActive = currentPath === item.href;
                                
                                return (
                                    <Button
                                        key={`${item.href}-${index}`}
                                        variant="ghost"
                                        asChild
                                        className={cn(
                                            'w-full justify-start h-12 border-2 transition-all',
                                            'font-heading font-black uppercase tracking-wide text-sm',
                                            isActive 
                                                ? 'bg-chart-1 border-border text-main-foreground shadow-shadow' 
                                                : 'bg-background border-border text-foreground hover:bg-chart-1 hover:text-main-foreground hover:shadow-shadow'
                                        )}
                                    >
                                        <Link href={item.href} prefetch>
                                            {Icon && <Icon className="h-4 w-4 mr-3" />}
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
                    <div className="border-2 border-border shadow-shadow bg-background p-6">
                        {children}
                    </div>
                </div>
            </div>
        </div>
    );
}