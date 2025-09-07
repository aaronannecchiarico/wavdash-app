import { cn } from '@/lib/utils';
import { forwardRef, type InputHTMLAttributes } from 'react';

interface BrutalistInputProps extends InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

const BrutalistInput = forwardRef<HTMLInputElement, BrutalistInputProps>(
  ({ className, type, hasError, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-12 w-full border-2 border-border bg-background px-4 py-3',
          'font-base font-bold text-foreground placeholder:text-foreground/50',
          'shadow-shadow transition-all duration-200',
          'focus:outline-none focus:shadow-none focus:translate-x-boxShadowX focus:translate-y-boxShadowY',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'hover:shadow-none hover:translate-x-boxShadowX hover:translate-y-boxShadowY',
          hasError && 'border-red-500 bg-red-50',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

BrutalistInput.displayName = 'BrutalistInput';

export { BrutalistInput };