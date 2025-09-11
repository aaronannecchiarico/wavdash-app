import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';
import { forwardRef, type InputHTMLAttributes } from 'react';

interface BrutalistCheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
    label?: string;
}

const BrutalistCheckbox = forwardRef<HTMLInputElement, BrutalistCheckboxProps>(({ className, label, id, ...props }, ref) => {
    return (
        <div className="flex items-center space-x-3">
            <div className="relative">
                <input type="checkbox" id={id} className="sr-only" ref={ref} {...props} />
                <div
                    className={cn(
                        'h-5 w-5 cursor-pointer border-2 border-border bg-background',
                        'flex items-center justify-center transition-all',
                        'shadow-shadow hover:translate-x-boxShadowX hover:translate-y-boxShadowY hover:shadow-none',
                        className,
                    )}
                    onClick={() => props.onChange?.({ target: { checked: !props.checked } } as React.ChangeEvent<HTMLInputElement>)}
                >
                    {props.checked && <Check className="h-3 w-3 text-foreground" />}
                </div>
            </div>
            {label && (
                <label htmlFor={id} className="cursor-pointer font-base font-bold text-foreground select-none">
                    {label}
                </label>
            )}
        </div>
    );
});

BrutalistCheckbox.displayName = 'BrutalistCheckbox';

export { BrutalistCheckbox };
