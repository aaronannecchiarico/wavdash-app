import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';
import { forwardRef, type InputHTMLAttributes } from 'react';

interface BrutalistCheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
}

const BrutalistCheckbox = forwardRef<HTMLInputElement, BrutalistCheckboxProps>(
  ({ className, label, id, ...props }, ref) => {
    return (
      <div className="flex items-center space-x-3">
        <div className="relative">
          <input
            type="checkbox"
            id={id}
            className="sr-only"
            ref={ref}
            {...props}
          />
          <div 
            className={cn(
              'w-5 h-5 border-2 border-border bg-background cursor-pointer',
              'flex items-center justify-center transition-all',
              'shadow-shadow hover:shadow-none hover:translate-x-boxShadowX hover:translate-y-boxShadowY',
              className
            )}
            onClick={() => props.onChange?.({target: {checked: !props.checked}} as any)}
          >
            {props.checked && (
              <Check className="h-3 w-3 text-foreground" />
            )}
          </div>
        </div>
        {label && (
          <label 
            htmlFor={id} 
            className="font-base font-bold text-foreground cursor-pointer select-none"
          >
            {label}
          </label>
        )}
      </div>
    );
  }
);

BrutalistCheckbox.displayName = 'BrutalistCheckbox';

export { BrutalistCheckbox };