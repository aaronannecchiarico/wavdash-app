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
                    'neo-border neo-transition px-3 py-2 text-xs font-black tracking-wide uppercase',
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

            <div className="space-y-6 p-4 sm:p-6 lg:p-8">
                {/* Neobrutalist Contest Table */}
                <div className="neo-border neo-shadow bg-neo-white dark:bg-neo-black">
                    <div className="bg-neo-black neo-border-b p-4">
                        <h2 className="text-neo-white text-xl font-black tracking-wider uppercase">BEAT BATTLES</h2>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-neo-yellow neo-border-b">
                                <tr>
                                    <th className="text-neo-black p-4 text-left font-black tracking-wide uppercase">CONTEST</th>
                                    <th className="text-neo-black p-4 text-left font-black tracking-wide uppercase">STATUS</th>
                                    <th className="text-neo-black p-4 text-left font-black tracking-wide uppercase">FIGHTERS</th>
                                    <th className="text-neo-black p-4 text-left font-black tracking-wide uppercase">DEADLINE</th>
                                    <th className="text-neo-black p-4 text-left font-black tracking-wide uppercase">ACTION</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.map((contest) => (
                                    <tr key={contest.id} className="neo-border-b hover:bg-neo-green/10">
                                        <td className="text-neo-black dark:text-neo-white p-4 font-bold">{contest.name.toUpperCase()}</td>
                                        <td className="p-4">
                                            <BrutalistStatusBadge status={contest.status} />
                                        </td>
                                        <td className="text-neo-black dark:text-neo-white p-4 font-mono font-bold">
                                            {contest.contest_users_count} PLAYERS
                                        </td>
                                        <td className="text-neo-black dark:text-neo-white p-4 font-mono font-bold">
                                            {new Date(contest.end_date).toLocaleDateString().toUpperCase()}
                                        </td>
                                        <td className="p-4">
                                            <Button variant="default" size="sm" className="neo-shadow font-black uppercase" asChild>
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
                            <p className="text-neo-white text-sm font-bold">
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
