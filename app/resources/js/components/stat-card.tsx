import { cn } from '@/lib/utils';
import React from 'react';

interface StatCardProps {
    title: string;
    value: string | number;
    icon?: React.ReactNode;
    className?: string;
}

export function StatCard({ title, value, icon, className }: StatCardProps) {
    return (
        <div className={cn('studio-card p-6 flex items-center gap-4', className)}>
            {icon && (
                <div className="flex h-10 w-10 items-center justify-center rounded-[--radius-md] bg-[--amber]/10 shrink-0 text-[--amber]">
                    {icon}
                </div>
            )}
            <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{title}</p>
                <p className="font-mono text-2xl font-medium text-foreground mt-0.5">{value}</p>
            </div>
        </div>
    );
}
