interface NeoToastProps {
  title?: string;
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  className?: string;
}

export function NeoToast({ title, message, type = 'info', className = '' }: NeoToastProps) {
  const colorMap = {
    success: 'bg-chart-1',
    error: 'bg-red-500',
    warning: 'bg-chart-3',
    info: 'bg-chart-4'
  };
  
  return (
    <div className={`border-2 border-border ${colorMap[type]} p-4 animate-slide-up ${className}`} style={{ boxShadow: 'var(--shadow)' }}>
      {title && (
        <h4 className="font-heading font-black uppercase text-main-foreground mb-1">{title}</h4>
      )}
      <p className="font-base font-bold text-main-foreground text-sm">{message}</p>
    </div>
  );
}