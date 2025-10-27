import { Appearance, useAppearance } from '@/hooks/use-appearance';
import { cn } from '@/lib/utils';
import { LucideIcon, Monitor, Moon, Sun } from 'lucide-react';
import { HTMLAttributes } from 'react';

export default function AppearanceToggleTab({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
    const { appearance, updateAppearance } = useAppearance();

    const tabs: { value: Appearance; icon: LucideIcon; label: string; color: string }[] = [
        { value: 'light', icon: Sun, label: 'Light', color: 'bg-[var(--neo-yellow)]' },
        { value: 'dark', icon: Moon, label: 'Dark', color: 'bg-[var(--neo-blue)]' },
        { value: 'system', icon: Monitor, label: 'System', color: 'bg-[var(--neo-green)]' },
    ];

    return (
        <div className={cn('inline-flex gap-2 p-2', className)} {...props}>
            {tabs.map(({ value, icon: Icon, label, color }) => (
                <button
                    key={value}
                    onClick={() => updateAppearance(value)}
                    className={cn(
                        'flex items-center gap-3 border-2 border-border px-6 py-4 font-black tracking-wide uppercase transition-all',
                        appearance === value
                            ? `${color} neo-shadow text-[var(--main-foreground)]`
                            : 'hover:neo-shadow-hover bg-background text-foreground hover:translate-x-1 hover:translate-y-1',
                    )}
                    style={{
                        boxShadow: appearance === value ? 'var(--shadow)' : 'none',
                        borderRadius: '0px',
                    }}
                >
                    <Icon className="h-5 w-5" />
                    <span className="text-sm">{label}</span>
                </button>
            ))}
        </div>
    );
}
