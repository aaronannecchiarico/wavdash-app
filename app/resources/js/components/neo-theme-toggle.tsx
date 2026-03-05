import { Button } from '@/components/ui/button';
import { useAppearance } from '@/hooks/use-appearance';
import { Monitor, Moon, Sun } from 'lucide-react';

export function NeoThemeToggle() {
    const { appearance, updateAppearance } = useAppearance();

    const handleThemeToggle = () => {
        if (appearance === 'light') {
            updateAppearance('dark');
        } else if (appearance === 'dark') {
            updateAppearance('system');
        } else {
            updateAppearance('light');
        }
    };

    const getIcon = () => {
        switch (appearance) {
            case 'light':
                return <Sun className="h-5 w-5 text-[var(--neo-black)]" />;
            case 'dark':
                return <Moon className="h-5 w-5 text-[var(--neo-white)]" />;
            case 'system':
                return <Monitor className="h-5 w-5 text-[var(--neo-black)]" />;
            default:
                return <Sun className="h-5 w-5 text-[var(--neo-black)]" />;
        }
    };

    const getButtonColor = () => {
        switch (appearance) {
            case 'light':
                return 'bg-[var(--neo-yellow)] dark:bg-[var(--neo-yellow)] border-[var(--neo-black)] dark:border-[var(--neo-black)]';
            case 'dark':
                return 'bg-[var(--neo-blue)] dark:bg-[var(--neo-blue)] border-[var(--neo-white)] dark:border-[var(--neo-white)]';
            case 'system':
                return 'bg-[var(--neo-green)] dark:bg-[var(--neo-green)] border-[var(--neo-black)] dark:border-[var(--neo-white)]';
            default:
                return 'bg-[var(--neo-yellow)] border-[var(--neo-black)]';
        }
    };

    return (
        <Button
            variant="secondary"
            size="icon"
            className={`neo-shadow hover:neo-shadow-hover ${getButtonColor()}`}
            onClick={handleThemeToggle}
            style={{ borderRadius: '0px' }}
        >
            {getIcon()}
        </Button>
    );
}
