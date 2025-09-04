import { Link } from '@inertiajs/react';
import { LayoutGrid, Music, PartyPopper } from 'lucide-react';

// Brutalist sidebar items with color assignments
const sidebarItems = [
    { label: 'DASHBOARD', icon: LayoutGrid, href: '/dashboard', color: 'bg-[var(--neo-green)]' },
    { label: 'MY TRACKS', icon: Music, href: '/uploads', color: 'bg-[var(--neo-pink)]' },
    { label: 'CONTESTS', icon: PartyPopper, href: '/contests', color: 'bg-[var(--neo-blue)]' },
];


export function AppSidebar() {
    return (
        <aside className="w-64 bg-[var(--neo-black)] neo-border-r">
            <div className="p-4 space-y-2">
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
        </aside>
    );
}
