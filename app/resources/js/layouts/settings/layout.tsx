import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { type NavItem } from '@/types';
import { Link, usePage } from '@inertiajs/react';
import { type PropsWithChildren } from 'react';

const sidebarNavItems: NavItem[] = [
    { title: 'Profile', href: '/settings/profile', icon: null },
    { title: 'Password', href: '/settings/password', icon: null },
    { title: 'Appearance', href: '/settings/appearance', icon: null },
];

export default function SettingsLayout({ children }: PropsWithChildren) {
    const { url } = usePage();
    const currentPath = url.split('?')[0];

    return (
        <div className="px-4 py-6 sm:px-6 lg:px-8">
            <div className="mb-6 border-b border-[--border] pb-6">
                <h1 className="font-serif text-2xl text-foreground mb-1">Settings</h1>
                <p className="text-sm text-muted-foreground">Manage your profile and account preferences</p>
            </div>

            <div className="flex flex-col space-y-8 lg:flex-row lg:space-y-0 lg:space-x-12">
                <aside className="w-full max-w-xl lg:w-48">
                    <nav className="flex flex-col space-y-0.5">
                        {sidebarNavItems.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                prefetch
                                className={cn(
                                    'flex items-center gap-2 px-3 py-2 rounded-[--radius-md] text-sm font-medium transition-all duration-150',
                                    currentPath === item.href
                                        ? 'bg-[--sidebar-accent] text-[--amber]'
                                        : 'text-muted-foreground hover:text-foreground hover:bg-muted',
                                )}
                            >
                                {item.title}
                            </Link>
                        ))}
                    </nav>
                </aside>

                <Separator className="my-6 md:hidden" />

                <div className="flex-1 md:max-w-2xl">
                    <section className="max-w-xl space-y-12">{children}</section>
                </div>
            </div>
        </div>
    );
}
