import { cn } from '@/lib/utils';
import { forwardRef, type LabelHTMLAttributes } from 'react';

const BrutalistLabel = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={cn(
          'font-heading font-black text-sm uppercase tracking-widest text-foreground',
          'mb-2 block',
          className
        )}
        {...props}
      />
    );
  }
);

BrutalistLabel.displayName = 'BrutalistLabel';

export { BrutalistLabel };