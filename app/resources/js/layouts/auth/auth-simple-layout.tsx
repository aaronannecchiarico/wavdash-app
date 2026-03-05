import { Link } from '@inertiajs/react';
import { Music } from 'lucide-react';
import { type PropsWithChildren } from 'react';

interface AuthLayoutProps {
    name?: string;
    title?: string;
    description?: string;
}

export default function AuthSimpleLayout({ children, title, description }: PropsWithChildren<AuthLayoutProps>) {
    return (
        <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-background p-6 md:p-10">
            <div className="w-full max-w-sm">
                <div className="flex flex-col gap-8">
                    <div className="flex flex-col items-center gap-4">
                        <Link href={route('home')} className="flex flex-col items-center gap-2">
                            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[--amber]">
                                <Music className="h-5 w-5 text-white" />
                            </div>
                            <span className="sr-only">WavDash</span>
                        </Link>

                        <div className="space-y-1.5 text-center">
                            <h1 className="font-serif text-2xl text-foreground">{title}</h1>
                            {description && <p className="text-sm text-muted-foreground">{description}</p>}
                        </div>
                    </div>
                    {children}
                </div>
            </div>
        </div>
    );
}
