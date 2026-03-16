import { icons, type LucideProps } from 'lucide-react';
import { createElement } from 'react';

interface IconProps extends Omit<LucideProps, 'ref'> {
  name: string;
  size?: number;
  className?: string;
}

export function Icon({ name, size = 24, className = "", ...props }: IconProps) {
  const IconComponent = icons[name as keyof typeof icons];
  if (!IconComponent) return null;
  return createElement(IconComponent, { size, className, ...props });
}
