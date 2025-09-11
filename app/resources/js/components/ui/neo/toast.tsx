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

  // Enhanced text color mapping for better readability
  const textColorMap = {
    success: 'text-black', // Dark text on bright green
    error: 'text-white',   // White text on red
    warning: 'text-black', // Dark text on bright yellow  
    info: 'text-white',    // White text on blue
    default: 'text-white'  // White text on pink
  };

  const buttonColorMap = {
    success: 'text-black border-black hover:bg-black hover:text-chart-1',
    error: 'text-white border-white hover:bg-white hover:text-red-500',
    warning: 'text-black border-black hover:bg-black hover:text-chart-3',
    info: 'text-white border-white hover:bg-white hover:text-chart-4',
    default: 'text-white border-white hover:bg-white hover:text-chart-2'
  };
  
  return (
    <div className={`border-2 border-border shadow-shadow ${colorMap[type]} p-4 animate-slide-up max-w-md ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          {title && (
            <h4 className={`font-heading font-black uppercase tracking-wide ${textColorMap[type]} text-sm mb-1`}>
              {title}
            </h4>
          )}
          <p className={`font-base font-bold ${textColorMap[type]} text-sm leading-relaxed`}>
            {message}
          </p>
        </div>
        
        {onDismiss && (
          <Button
            variant="neutral" 
            size="sm"
            className={`${buttonColorMap[type]} border-2 ml-3 h-8 w-8 p-0`}
            onClick={onDismiss}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      
      {action && (
        <div className="mt-3">
          <Button
            variant="neutral"
            size="sm"
            className={`font-heading font-black uppercase tracking-wide ${buttonColorMap[type]}`}
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