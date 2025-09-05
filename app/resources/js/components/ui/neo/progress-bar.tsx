interface NeoProgressBarProps {
  value: number;
  max?: number;
  color?: string;
  className?: string;
}

export function NeoProgressBar({ value, max = 100, color = 'bg-chart-1', className = '' }: NeoProgressBarProps) {
  const percentage = (value / max) * 100;
  
  return (
    <div className={`border-2 border-border bg-background h-8 ${className}`} style={{ boxShadow: 'var(--shadow)' }}>
      <div 
        className={`h-full ${color} border-r-2 border-border transition-all duration-300 flex items-center justify-end pr-2`}
        style={{ width: `${percentage}%` }}
      >
        <span className="font-heading font-black text-xs text-main-foreground">
          {Math.round(percentage)}%
        </span>
      </div>
    </div>
  );
}