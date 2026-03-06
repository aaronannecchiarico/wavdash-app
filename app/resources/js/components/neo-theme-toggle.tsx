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
                return <Sun className="h-4 w-4" />;
            case 'dark':
                return <Moon className="h-4 w-4" />;
            case 'system':
                return <Monitor className="h-4 w-4" />;
            default:
                return <Sun className="h-4 w-4" />;
        }
    };

    return (
        <Button
            variant="ghost"
            size="icon"
            className="rounded-[--radius-md] text-muted-foreground hover:text-foreground"
            onClick={handleThemeToggle}
            aria-label="Toggle theme"
        >
            {getIcon()}
        </Button>
    );
}
