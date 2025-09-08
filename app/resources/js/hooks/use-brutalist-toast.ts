import { toast as sonnerToast } from "sonner";

interface BrutalistToastOptions {
  title?: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  duration?: number;
}

interface BrutalistToastHook {
  success: (options: BrutalistToastOptions) => string | number;
  error: (options: BrutalistToastOptions) => string | number;
  warning: (options: BrutalistToastOptions) => string | number;
  info: (options: BrutalistToastOptions) => string | number;
  default: (options: BrutalistToastOptions) => string | number;
  dismiss: (toastId?: string | number) => void;
}

const useBrutalistToast = (): BrutalistToastHook => {
  const createToast = (type: 'success' | 'error' | 'warning' | 'info' | 'default') => 
    ({ title, description, action, duration }: BrutalistToastOptions) => {
      const toastOptions = {
        duration: duration || 5000,
        action: action ? {
          label: action.label.toUpperCase(),
          onClick: action.onClick,
        } : undefined,
        style: {
          backgroundColor: getTypeColor(type),
          borderColor: 'var(--border)',
          color: 'var(--main-foreground)',
        }
      };

      switch (type) {
        case 'success':
          return sonnerToast.success(title || 'SUCCESS', {
            description: description.toUpperCase(),
            ...toastOptions,
          });
        case 'error':
          return sonnerToast.error(title || 'ERROR', {
            description: description.toUpperCase(),
            ...toastOptions,
          });
        case 'warning':
          return sonnerToast.warning(title || 'WARNING', {
            description: description.toUpperCase(),
            ...toastOptions,
          });
        case 'info':
          return sonnerToast.info(title || 'INFO', {
            description: description.toUpperCase(),
            ...toastOptions,
          });
        default:
          return sonnerToast(title || 'NOTIFICATION', {
            description: description.toUpperCase(),
            ...toastOptions,
          });
      }
    };

  const getTypeColor = (type: string) => {
    const colorMap = {
      success: 'var(--chart-1)',
      error: '#ef4444',
      warning: 'var(--chart-3)',
      info: 'var(--chart-4)',
      default: 'var(--chart-2)',
    };
    return colorMap[type as keyof typeof colorMap] || colorMap.default;
  };

  return {
    success: createToast('success'),
    error: createToast('error'),
    warning: createToast('warning'),
    info: createToast('info'),
    default: createToast('default'),
    dismiss: sonnerToast.dismiss,
  };
};

export { useBrutalistToast };