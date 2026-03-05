import { type SharedData } from '@/types';
import { Link, usePage } from '@inertiajs/react';
import { Music } from 'lucide-react';
import { type PropsWithChildren } from 'react';

interface AuthLayoutProps {
    title?: string;
    description?: string;
}

export default function AuthSplitLayout({ children, title, description }: PropsWithChildren<AuthLayoutProps>) {
    const { name } = usePage<SharedData>().props;

    return (
        <div className="grid min-h-dvh lg:grid-cols-2">
            {/* Left brand panel */}
            <div className="relative hidden lg:flex flex-col bg-[--surface-2] p-12">
                <div className="gradient-mesh absolute inset-0 pointer-events-none" />
                <Link href={route('home')} className="relative z-10 flex items-center gap-2.5">
                    <div className="flex h-8 w-8 rounded-full bg-[--amber] items-center justify-center shrink-0">
                        <Music className="h-4 w-4 text-white" />
                    </div>
                    <span className="font-sans font-semibold text-base text-foreground">{name ?? 'WavDash'}</span>
                </Link>
                <div className="relative z-10 mt-auto">
                    <h2 className="font-serif text-4xl text-foreground mb-4 leading-tight">
                        Precision audio intelligence for serious producers.
                    </h2>
                    <blockquote className="mt-8 border-l-2 border-[--amber] pl-4">
                        <p className="text-base text-muted-foreground italic">
                            "From upload to insight in seconds. WavDash is the tool I didn't know I needed."
                        </p>
                        <footer className="text-sm text-muted-foreground mt-2">— Beta tester</footer>
                    </blockquote>
                </div>
            </div>

            {/* Right form panel */}
            <div className="flex items-center justify-center p-8 bg-background">
                <div className="w-full max-w-sm space-y-6">
                    {/* Mobile logo */}
                    <Link href={route('home')} className="flex items-center justify-center gap-2.5 lg:hidden mb-8">
                        <div className="h-8 w-8 rounded-full bg-[--amber] flex items-center justify-center">
                            <Music className="h-4 w-4 text-white" />
                        </div>
                        <span className="font-sans font-semibold text-base text-foreground">{name ?? 'WavDash'}</span>
                    </Link>

                    <div>
                        <h1 className="text-2xl font-serif text-foreground">{title}</h1>
                        {description && (
                            <p className="text-sm text-muted-foreground mt-1">{description}</p>
                        )}
                    </div>
                    {children}
                </div>
            </div>
        </div>
    );
}
