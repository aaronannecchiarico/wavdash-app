import { BrutalistStatusBadge } from '@/components/brutalist-status-badge';
import { Button } from '@/components/ui/neo/button';
import AppLayout from '@/layouts/app-layout';
import { cn } from '@/lib/utils';
import { PaginatedData, User, type BreadcrumbItem } from '@/types';
import { Head, Link } from '@inertiajs/react';
import React from 'react';

interface Contest {
    id: number;
    name: string;
    description: string;
    start_date: string;
    end_date: string;
    status: 'Upcoming' | 'Active' | 'Finished';
    user: {
        id: number;
        name: string;
    };
    contest_users_count: number;
}

interface PaginationLink {
    url: string | null;
    label: string;
    active: boolean;
}

interface Props {
    auth: {
        user: User;
    };
    contests: PaginatedData<Contest>;
}

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Contests',
        href: '/contests',
    },
];

const Pagination: React.FC<{ links: PaginationLink[] }> = ({ links }) => (
    <nav className="mt-6 flex justify-center gap-2">
        {links.map((link) => (
            <Link
                key={link.label}
                href={link.url ?? ''}
                preserveScroll
                className={cn(
                    'neo-border px-3 py-2 text-xs font-black uppercase tracking-wide neo-transition',
                    link.active 
                        ? 'bg-neo-black text-neo-white' 
                        : 'bg-neo-white text-neo-black hover:bg-neo-green hover:translate-x-1 hover:translate-y-1',
                    !link.url && 'cursor-not-allowed opacity-50',
                )}
                dangerouslySetInnerHTML={{ __html: link.label }}
            />
        ))}
    </nav>
);

const ContestIndex: React.FC<Props> = ({ contests }) => {
    const { data, meta } = contests;

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Contests" />

            <div className="p-4 sm:p-6 lg:p-8 space-y-6">
                {/* Neobrutalist Contest Table */}
                <div className="neo-border neo-shadow bg-neo-white dark:bg-neo-black">
                    <div className="bg-neo-black p-4 neo-border-b">
                        <h2 className="text-xl font-black uppercase tracking-wider text-neo-white">
                            BEAT BATTLES
                        </h2>
                    </div>
                    
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-neo-yellow neo-border-b">
                                <tr>
                                    <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">CONTEST</th>
                                    <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">STATUS</th>
                                    <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">FIGHTERS</th>
                                    <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">DEADLINE</th>
                                    <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">ACTION</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.map((contest) => (
                                    <tr key={contest.id} className="neo-border-b hover:bg-neo-green/10">
                                        <td className="p-4 font-bold text-neo-black dark:text-neo-white">
                                            {contest.name.toUpperCase()}
                                        </td>
                                        <td className="p-4">
                                            <BrutalistStatusBadge status={contest.status} />
                                        </td>
                                        <td className="p-4 font-mono font-bold text-neo-black dark:text-neo-white">
                                            {contest.contest_users_count} PLAYERS
                                        </td>
                                        <td className="p-4 font-mono font-bold text-neo-black dark:text-neo-white">
                                            {new Date(contest.end_date).toLocaleDateString().toUpperCase()}
                                        </td>
                                        <td className="p-4">
                                            <Button 
                                                variant="accent" 
                                                size="sm"
                                                className="font-black uppercase neo-shadow"
                                                asChild
                                            >
                                                <Link href={`/contests/${contest.id}`}>ENTER</Link>
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    
                    {/* Brutalist Pagination Footer */}
                    <div className="neo-border-t bg-neo-pink p-4">
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-bold text-neo-white">
                                SHOWING {meta.from} TO {meta.to} OF {meta.total} RESULTS
                            </p>
                            <Pagination links={meta.links} />
                        </div>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
};

export default ContestIndex;
