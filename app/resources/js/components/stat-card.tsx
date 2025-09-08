import { Card, CardContent } from '@/components/ui/neo/card';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  color?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({ title, value, color = 'bg-main', icon, className }: StatCardProps) {
  return (
    <Card className={cn('transition-all hover:translate-x-1 hover:translate-y-1', className)}>
      <CardContent className={cn('p-6', color)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {icon && (
              <div className="w-12 h-12 flex items-center justify-center">
                {icon}
              </div>
            )}
            <div>
              <h3 className="font-heading font-black uppercase tracking-widest text-main-foreground text-sm">
                {title}
              </h3>
              <p className="font-heading font-black text-2xl text-main-foreground">
                {value}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}