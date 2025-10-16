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
            backgroundSize: '20px 20px',
        }}
    />
);

export default function BrutalistAuthLayout({ children, title, description }: PropsWithChildren<BrutalistAuthLayoutProps>) {
    return (
        <div className="relative flex min-h-screen items-center justify-center bg-chart-3 p-6">
            <GridPattern />

            {/* Back to home link */}
            <div className="absolute top-6 left-6 z-20">
                <Link
                    href={route('home')}
                    className="flex items-center gap-2 border-2 border-border bg-background p-3 shadow-shadow transition-all hover:translate-x-boxShadowX hover:translate-y-boxShadowY hover:shadow-none"
                >
                    <Music className="h-5 w-5 text-foreground" />
                    <span className="font-heading text-sm font-black tracking-wide text-foreground uppercase">WAVDASH</span>
                </Link>
            </div>

            <div className="z-10 w-full max-w-md">
                <div className="border-2 border-border bg-background p-8 shadow-shadow">
                    {/* Header */}
                    <div className="mb-8 text-center">
                        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center border-2 border-border bg-chart-1 shadow-shadow">
                            <Music className="h-8 w-8 text-main-foreground" />
                        </div>

                        <h1 className="mb-2 font-heading text-2xl font-black tracking-widest text-foreground uppercase">{title}</h1>

                        {description && <p className="text-sm font-base font-bold tracking-wide text-foreground/70 uppercase">{description}</p>}
                    </div>

                    {/* Form Content */}
                    <div className="space-y-6">{children}</div>
                </div>
            </div>
        </div>
    );
}
