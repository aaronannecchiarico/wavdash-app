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
        <aside className="w-64 bg-[var(--neo-black)] neo-border-r flex flex-col">
            {/* Brand Header */}
            <div className="p-6 border-b-2 border-border">
                <h1 className="text-xl font-heading font-black uppercase tracking-widest text-[var(--neo-white)]">
                    Beat Forge
                </h1>
            </div>

            {/* Navigation Items */}
            <div className="p-4 space-y-2 flex-1">
                {sidebarItems.map((item) => (
                    <Link
                        key={item.label}
                        href={item.href}
                        className={`${item.color} text-[var(--neo-black)] font-black uppercase tracking-wide neo-shadow hover:neo-shadow-hover hover:translate-x-1 hover:translate-y-1 transition-all flex items-center gap-3 p-4 block`}
                    >
                        <item.icon className="w-5 h-5" />
                        {item.label}
                    </Link>
                ))}
            </div>

            {/* User Menu - Bottom of Sidebar */}
            <div className="p-4 border-t-2 border-border">
                <NavUser />
            </div>
        </aside>
    );
}
