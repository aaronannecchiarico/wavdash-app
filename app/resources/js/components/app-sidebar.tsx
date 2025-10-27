import { Link } from '@inertiajs/react';
import { LayoutGrid, Music, PartyPopper } from 'lucide-react';
import { NavUser } from './nav-user';

// Brutalist sidebar items with color assignments
const sidebarItems = [
    { label: 'DASHBOARD', icon: LayoutGrid, href: '/dashboard', color: 'bg-[var(--neo-green)]' },
    { label: 'MY TRACKS', icon: Music, href: '/uploads', color: 'bg-[var(--neo-pink)]' },
    { label: 'CONTESTS', icon: PartyPopper, href: '/contests', color: 'bg-[var(--neo-blue)]' },
];

export function AppSidebar() {
    return (
        <aside className="neo-border-r flex w-64 flex-col bg-[var(--neo-black)]">
            {/* Brand Header */}
            <div className="border-b-2 border-border p-6">
                <h1 className="font-heading text-xl font-black tracking-widest text-[var(--neo-white)] uppercase">WavDash</h1>
            </div>

            {/* Navigation Items */}
            <div className="flex-1 space-y-2 p-4">
                {sidebarItems.map((item) => (
                    <Link
                        key={item.label}
                        href={item.href}
                        className={`${item.color} neo-shadow hover:neo-shadow-hover block flex items-center gap-3 p-4 font-black tracking-wide text-[var(--neo-black)] uppercase transition-all hover:translate-x-1 hover:translate-y-1`}
                    >
                        <item.icon className="h-5 w-5" />
                        {item.label}
                    </Link>
                ))}
            </div>

            {/* User Menu - Bottom of Sidebar */}
            <div className="border-t-2 border-border p-4">
                <NavUser />
            </div>
        </aside>
    );
}
