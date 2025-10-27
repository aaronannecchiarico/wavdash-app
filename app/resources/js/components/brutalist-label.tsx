import { cn } from '@/lib/utils';
import { forwardRef, type LabelHTMLAttributes } from 'react';

const BrutalistLabel = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(({ className, ...props }, ref) => {
    return (
        <label
            ref={ref}
            className={cn('font-heading text-sm font-black tracking-widest text-foreground uppercase', 'mb-2 block', className)}
            {...props}
        />
    );
});

BrutalistLabel.displayName = 'BrutalistLabel';

export { BrutalistLabel };
