import { Breadcrumbs } from '@/components/breadcrumbs';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { UserMenuContent } from '@/components/user-menu-content';
import { type BreadcrumbItem, type SharedData } from '@/types';
import { Link, usePage } from '@inertiajs/react';
import { LayoutGrid, Menu, Music, PartyPopper } from 'lucide-react';

const mobileNavItems = [
    { title: 'Dashboard', href: '/dashboard', icon: LayoutGrid },
    { title: 'My tracks', href: '/uploads', icon: Music },
    { title: 'Contests', href: '/contests', icon: PartyPopper },
];

interface AppHeaderProps {
    breadcrumbs?: BreadcrumbItem[];
}

export function AppHeader({ breadcrumbs = [] }: AppHeaderProps) {
    const { auth } = usePage<SharedData>().props;

    return (
        <>
            <header className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b border-[--border]">
                <div className="flex h-14 items-center px-6 gap-4">
                    {/* Mobile menu */}
                    <div className="lg:hidden">
                        <Sheet>
                            <SheetTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                    <Menu className="h-4 w-4" />
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="left" className="w-64 p-0">
                                <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
                                <SheetHeader className="px-5 py-5 border-b border-[--border]">
                                    <div className="flex items-center gap-2.5">
                                        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[--amber] shrink-0">
                                            <Music className="h-4 w-4 text-white" />
                                        </div>
                                        <span className="font-sans text-base font-semibold text-foreground tracking-tight">WavDash</span>
                                    </div>
                                </SheetHeader>
                                <nav className="space-y-0.5 px-3 py-4">
                                    {mobileNavItems.map((item) => (
                                        <Link
                                            key={item.title}
                                            href={item.href}
                                            className="flex items-center gap-3 px-3 py-2.5 rounded-[--radius-md] text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                                        >
                                            <item.icon className="h-4 w-4 shrink-0" />
                                            {item.title}
                                        </Link>
                                    ))}
                                </nav>
                            </SheetContent>
                        </Sheet>
                    </div>

                    {/* Breadcrumbs */}
                    <div className="flex-1">
                        {breadcrumbs.length > 0 && <Breadcrumbs breadcrumbs={breadcrumbs} />}
                    </div>

                    {/* User menu */}
                    <div className="flex items-center gap-2">
                        <UserMenuContent user={auth.user} />
                    </div>
                </div>
            </header>
        </>
    );
}
