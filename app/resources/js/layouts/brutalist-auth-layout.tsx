import { Link } from '@inertiajs/react';
import { Music } from 'lucide-react';
import { type PropsWithChildren } from 'react';

interface BrutalistAuthLayoutProps {
  title?: string;
  description?: string;
}

// Grid pattern background component
const GridPattern = () => (
  <div 
    className="absolute inset-0 opacity-10"
    style={{
      backgroundImage: `
        linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)
      `,
      backgroundSize: '20px 20px'
    }}
  />
);

export default function BrutalistAuthLayout({ children, title, description }: PropsWithChildren<BrutalistAuthLayoutProps>) {
  return (
    <div className="min-h-screen bg-chart-3 flex items-center justify-center relative p-6">
      <GridPattern />
      
      {/* Back to home link */}
      <div className="absolute top-6 left-6 z-20">
        <Link 
          href={route('home')}
          className="flex items-center gap-2 border-2 border-border bg-background shadow-shadow hover:shadow-none hover:translate-x-boxShadowX hover:translate-y-boxShadowY transition-all p-3"
        >
          <Music className="h-5 w-5 text-foreground" />
          <span className="font-heading font-black text-sm uppercase tracking-wide text-foreground">
            BEAT FORGE
          </span>
        </Link>
      </div>

      <div className="w-full max-w-md z-10">
        <div className="border-2 border-border shadow-shadow bg-background p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-chart-1 border-2 border-border shadow-shadow flex items-center justify-center">
              <Music className="h-8 w-8 text-main-foreground" />
            </div>
            
            <h1 className="text-2xl font-heading font-black uppercase tracking-widest text-foreground mb-2">
              {title}
            </h1>
            
            {description && (
              <p className="font-base font-bold text-foreground/70 uppercase tracking-wide text-sm">
                {description}
              </p>
            )}
          </div>

          {/* Form Content */}
          <div className="space-y-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}