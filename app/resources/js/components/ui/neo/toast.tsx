import { X } from 'lucide-react';
import { Button } from './button';

interface BrutalistToastAction {
  label: string;
  onClick: () => void;
}

interface BrutalistToastProps {
  title?: string;
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info' | 'default';
  action?: BrutalistToastAction;
  onDismiss?: () => void;
  className?: string;
}

export function BrutalistToast({ 
  title, 
  message, 
  type = 'default', 
  action, 
  onDismiss,
  className = '' 
}: BrutalistToastProps) {
  const colorMap = {
    success: 'bg-chart-1',
    error: 'bg-red-500',
    warning: 'bg-chart-3',
    info: 'bg-chart-4',
    default: 'bg-chart-2'
  };
  
  return (
    <div className={`border-2 border-border shadow-shadow ${colorMap[type]} p-4 animate-slide-up max-w-md ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          {title && (
            <h4 className="font-heading font-black uppercase tracking-wide text-main-foreground text-sm mb-1">
              {title}
            </h4>
          )}
          <p className="font-base font-bold text-main-foreground text-sm">
            {message}
          </p>
        </div>
        
        {onDismiss && (
          <Button
            variant="ghost" 
            size="sm"
            className="text-main-foreground hover:bg-main-foreground hover:text-background border-2 border-border ml-3 h-8 w-8 p-0"
            onClick={onDismiss}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      
      {action && (
        <div className="mt-3">
          <Button
            variant="outline"
            size="sm"
            className="font-heading font-black uppercase tracking-wide border-main-foreground text-main-foreground hover:bg-main-foreground hover:text-background"
            onClick={action.onClick}
          >
            {action.label}
          </Button>
        </div>
      )}
    </div>
  );
}

// Legacy export for backwards compatibility
export { BrutalistToast as NeoToast };