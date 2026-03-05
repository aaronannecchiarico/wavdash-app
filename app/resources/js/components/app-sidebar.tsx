import { cn } from '@/lib/utils';
import { Link, usePage } from '@inertiajs/react';
import { LayoutGrid, Music, PartyPopper } from 'lucide-react';
import { NavUser } from './nav-user';

const sidebarItems = [
    { label: 'Dashboard', icon: LayoutGrid, href: '/dashboard' },
    { label: 'My tracks', icon: Music, href: '/uploads' },
    { label: 'Contests', icon: PartyPopper, href: '/contests' },
];

export function AppSidebar() {
    const { url } = usePage();
    const currentPath = url.split('?')[0];

    return (
        <aside className="flex w-60 shrink-0 flex-col bg-sidebar border-r border-[--border] h-full">
            {/* Brand header */}
            <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[--border]">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[--amber] shrink-0">
                    <Music className="h-4 w-4 text-white" />
                </div>
                <span className="font-sans text-base font-semibold text-sidebar-foreground tracking-tight">WavDash</span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-0.5 px-3 py-4">
                {sidebarItems.map((item) => {
                    const isActive = currentPath === item.href || currentPath.startsWith(item.href + '/');
                    return (
                        <Link
                            key={item.label}
                            href={item.href}
                            className={cn(
                                'flex items-center gap-3 px-3 py-2.5 rounded-[--radius-md] text-sm font-medium transition-all duration-150',
                                isActive
                                    ? 'bg-[--sidebar-accent] text-[--amber] border-l-[3px] border-[--amber] pl-[calc(0.75rem-3px)]'
                                    : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                            )}
                        >
                            <item.icon className="h-4 w-4 shrink-0" />
                            {item.label}
                        </Link>
                    );
                })}
            </nav>

            {/* User menu */}
            <div className="border-t border-[--border] p-3">
                <NavUser />
            </div>
        </aside>
    );
}
