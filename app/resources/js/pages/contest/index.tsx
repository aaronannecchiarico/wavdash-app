import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
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
    <nav className="mt-4 flex justify-center">
        {links.map((link) => (
            <Link
                key={link.label}
                href={link.url ?? ''}
                preserveScroll
                className={cn(
                    'flex h-8 items-center justify-center rounded-md px-3 text-sm font-medium',
                    link.active ? 'bg-primary text-primary-foreground' : 'text-foreground hover:bg-accent',
                    !link.url && 'cursor-not-allowed text-muted-foreground',
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

            <div className="flex h-full flex-1 flex-col gap-4 overflow-x-auto rounded-xl p-4">
                <Card>
                    <CardHeader>
                        <CardTitle>All Contests</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Participants</TableHead>
                                    <TableHead>Ends On</TableHead>
                                    <TableHead></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {data.map((contest) => (
                                    <TableRow key={contest.id}>
                                        <TableCell className="font-medium">{contest.name}</TableCell>
                                        <TableCell>
                                            <Badge
                                                variant={
                                                    contest.status === 'Active'
                                                        ? 'default'
                                                        : contest.status === 'Finished'
                                                          ? 'destructive'
                                                          : 'secondary'
                                                }
                                            >
                                                {contest.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{contest.contest_users_count}</TableCell>
                                        <TableCell>{new Date(contest.end_date).toLocaleDateString()}</TableCell>
                                        <TableCell className="text-right">
                                            <Button asChild>
                                                <Link href={`/contests/${contest.id}`}>View</Link>
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                        <div className="mt-4 flex items-center justify-between">
                            <p className="text-sm text-muted-foreground">
                                Showing {meta.from} to {meta.to} of {meta.total} results
                            </p>
                            <Pagination links={meta.links} />
                        </div>
                    </CardContent>
                </Card>
            </div>
        </AppLayout>
    );
};

export default ContestIndex;
