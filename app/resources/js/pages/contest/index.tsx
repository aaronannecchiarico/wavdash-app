import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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

const statusVariantMap = {
    Active:   'success',
    Upcoming: 'warning',
    Finished: 'secondary',
} as const;

const Pagination: React.FC<{ links: PaginationLink[] }> = ({ links }) => (
    <nav className="mt-6 flex justify-center gap-2 flex-wrap">
        {links.map((link) => (
            <Link
                key={link.label}
                href={link.url ?? ''}
                preserveScroll
                className={cn(
                    'inline-flex items-center justify-center px-3 py-1.5 text-xs font-medium rounded-[--radius-md] transition-all duration-150 border',
                    link.active
                        ? 'bg-primary text-primary-foreground border-primary/20'
                        : 'bg-card text-foreground border-[--border-strong] hover:bg-muted',
                    !link.url && 'cursor-not-allowed opacity-50 pointer-events-none',
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
                <div className="studio-card overflow-hidden p-0">
                    {/* Header */}
                    <div className="px-6 py-4 border-b border-[--border]">
                        <h2 className="font-sans text-lg font-semibold text-foreground">Beat Battles</h2>
                        <p className="text-sm text-muted-foreground">Join a contest and compete with other producers</p>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[--surface-2]">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Contest</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Fighters</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Deadline</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[--border]">
                                {data.map((contest) => (
                                    <tr key={contest.id} className="hover:bg-[--surface-2] transition-colors">
                                        <td className="px-6 py-4 font-medium text-sm text-foreground">{contest.name}</td>
                                        <td className="px-6 py-4">
                                            <Badge variant={statusVariantMap[contest.status]}>{contest.status}</Badge>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-sm text-muted-foreground">
                                            {contest.contest_users_count} players
                                        </td>
                                        <td className="px-6 py-4 font-mono text-sm text-muted-foreground">
                                            {new Date(contest.end_date).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <Button variant="secondary" size="sm" asChild>
                                                <Link href={`/contests/${contest.id}`}>Enter</Link>
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination footer */}
                    <div className="px-6 py-4 border-t border-[--border] bg-[--surface-2]">
                        <div className="flex items-center justify-between flex-wrap gap-3">
                            <p className="text-sm text-muted-foreground">
                                Showing {meta.from}–{meta.to} of {meta.total} results
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
