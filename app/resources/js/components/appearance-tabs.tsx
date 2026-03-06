import { Appearance, useAppearance } from '@/hooks/use-appearance';
import { cn } from '@/lib/utils';
import { LucideIcon, Monitor, Moon, Sun } from 'lucide-react';
import { HTMLAttributes } from 'react';

export default function AppearanceToggleTab({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
    const { appearance, updateAppearance } = useAppearance();

    const tabs: { value: Appearance; icon: LucideIcon; label: string }[] = [
        { value: 'light', icon: Sun, label: 'Light' },
        { value: 'dark', icon: Moon, label: 'Dark' },
        { value: 'system', icon: Monitor, label: 'System' },
    ];

    return (
        <div className={cn('inline-flex rounded-[--radius-lg] border border-[--border-strong] p-1 bg-muted gap-0.5', className)} {...props}>
            {tabs.map(({ value, icon: Icon, label }) => (
                <button
                    key={value}
                    onClick={() => updateAppearance(value)}
                    className={cn(
                        'flex items-center gap-2 px-4 py-1.5 rounded-[--radius-md] text-sm font-medium transition-all duration-200',
                        appearance === value
                            ? 'bg-background text-foreground shadow-sm-studio'
                            : 'text-muted-foreground hover:text-foreground',
                    )}
                >
                    <Icon className="h-4 w-4" />
                    {label}
                </button>
            ))}
        </div>
    );
}
