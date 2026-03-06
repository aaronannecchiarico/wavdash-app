import { Button } from '@/components/ui/button';
import { type SharedData } from '@/types';
import { Head, Link, usePage } from '@inertiajs/react';
import { BarChart3, Gauge, Music, Scissors } from 'lucide-react';

const features = [
    {
        icon: BarChart3,
        title: 'Audio analysis',
        description: 'Extract key, BPM, loudness, and timbral characteristics from any audio file in seconds.',
        accent: 'bg-[--amber]/10 text-[--amber]',
    },
    {
        icon: Scissors,
        title: 'Stem separation',
        description: 'Isolate vocals, drums, bass, and instruments into individual tracks with AI precision.',
        accent: 'bg-[--jade]/10 text-[--jade]',
    },
    {
        icon: Gauge,
        title: 'Tempo effects',
        description: 'Generate pitch-perfect speed variations without artifacts — from 0.5× to 2× and beyond.',
        accent: 'bg-[--amber]/10 text-[--amber]',
    },
];

export default function Welcome() {
    const { auth } = usePage<SharedData>().props;

    return (
        <>
            <Head title="WavDash — Precision audio intelligence">
                <meta
                    name="description"
                    content="Professional stem separation, BPM analysis, and audio processing for producers who demand precision."
                />
            </Head>

            <div className="min-h-screen bg-background text-foreground">
                {/* Header */}
                <header className="sticky top-0 z-50 border-b border-[--border] bg-background/90 backdrop-blur-md">
                    <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
                        <div className="flex items-center gap-2.5">
                            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[--amber] shrink-0">
                                <Music className="h-4 w-4 text-white" />
                            </div>
                            <span className="font-sans text-base font-semibold text-foreground">WavDash</span>
                        </div>

                        <nav className="flex items-center gap-3">
                            {auth.user ? (
                                <Button variant="default" size="sm" asChild>
                                    <Link href={route('dashboard')}>Dashboard</Link>
                                </Button>
                            ) : (
                                <>
                                    <Button variant="ghost" size="sm" asChild>
                                        <Link href={route('login')}>Sign in</Link>
                                    </Button>
                                    <Button variant="default" size="sm" asChild>
                                        <Link href={route('register')}>Get started</Link>
                                    </Button>
                                </>
                            )}
                        </nav>
                    </div>
                </header>

                {/* Hero */}
                <section className="relative flex min-h-[calc(100vh-3.5rem)] items-center justify-center overflow-hidden px-6 py-24">
                    {/* Gradient mesh */}
                    <div className="gradient-mesh absolute inset-0 pointer-events-none" />
                    {/* Grain overlay */}
                    <div
                        className="absolute inset-0 pointer-events-none opacity-[0.025]"
                        style={{
                            backgroundImage:
                                "url(\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
                            backgroundRepeat: 'repeat',
                            backgroundSize: '128px 128px',
                        }}
                    />

                    <div className="relative z-10 text-center max-w-3xl mx-auto">
                        <div className="mx-auto mb-10 flex h-16 w-16 items-center justify-center rounded-full bg-[--amber] shadow-amber">
                            <Music className="h-8 w-8 text-white" />
                        </div>

                        <h1
                            className="font-serif text-5xl text-foreground mb-6 md:text-6xl lg:text-7xl"
                            style={{ letterSpacing: '-0.025em', lineHeight: 1.1 }}
                        >
                            Precision audio<br />intelligence.
                        </h1>

                        <p className="mx-auto mb-10 max-w-xl text-lg text-muted-foreground leading-relaxed md:text-xl">
                            Professional stem separation, BPM analysis, and audio processing for producers who demand precision.
                        </p>

                        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
                            <Button size="lg" className="px-7 py-3.5 shadow-amber hover:scale-[1.01] transition-all" asChild>
                                <Link href={auth.user ? route('uploads.create') : route('register')}>
                                    {auth.user ? 'Upload a track' : 'Get started free'}
                                </Link>
                            </Button>
                            <Button
                                variant="outline"
                                size="lg"
                                className="px-7 py-3.5 hover:scale-[1.01] transition-all"
                                asChild
                            >
                                <Link href={auth.user ? route('dashboard') : route('login')}>
                                    {auth.user ? 'Go to dashboard' : 'Sign in'}
                                </Link>
                            </Button>
                        </div>
                    </div>
                </section>

                {/* Features */}
                <section className="border-t border-[--border] bg-[--surface-2] px-6 py-20">
                    <div className="mx-auto max-w-6xl">
                        <div className="mb-14 text-center">
                            <h2 className="font-serif text-3xl text-foreground mb-3 md:text-4xl">What WavDash does</h2>
                            <p className="text-muted-foreground text-base">From upload to insight in seconds.</p>
                        </div>

                        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                            {features.map((feature) => {
                                const Icon = feature.icon;
                                return (
                                    <div key={feature.title} className="studio-card p-8 flex flex-col">
                                        <div className={`flex h-10 w-10 items-center justify-center rounded-[--radius-md] mb-6 ${feature.accent}`}>
                                            <Icon className="h-5 w-5" />
                                        </div>
                                        <h3 className="font-sans font-semibold text-base text-foreground mb-3">{feature.title}</h3>
                                        <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </section>

                {/* Demo waveform section */}
                <section className="border-t border-[--border] px-6 py-20">
                    <div className="mx-auto max-w-2xl text-center">
                        <h2 className="font-serif text-3xl text-foreground mb-4 md:text-4xl">Hear your music differently.</h2>
                        <p className="text-muted-foreground mb-12 text-base">
                            Upload any audio file and get instant analysis, stems, and tempo insights — all in your browser.
                        </p>

                        {/* Static waveform mockup */}
                        <div className="studio-card p-6 mb-10">
                            <div className="flex h-24 items-end justify-center gap-0.5 mb-4">
                                {[...Array(48)].map((_, i) => {
                                    const h = 8 + Math.abs(Math.sin(i * 2.5 + 1.3) * 70);
                                    return (
                                        <div
                                            key={i}
                                            className="w-1.5 rounded-full bg-[--amber]/50"
                                            style={{ height: `${h}px` }}
                                        />
                                    );
                                })}
                            </div>
                            <div className="grid grid-cols-3 gap-3">
                                {[
                                    { label: 'BPM', value: '128', color: 'text-[--amber]' },
                                    { label: 'Key', value: 'C# min', color: 'text-[--jade]' },
                                    { label: 'Loudness', value: '−8.2 dB', color: 'text-foreground' },
                                ].map((stat) => (
                                    <div key={stat.label} className="rounded-[--radius-md] bg-[--surface-2] p-3 text-center">
                                        <div className={`font-mono font-medium text-lg ${stat.color}`}>{stat.value}</div>
                                        <div className="text-xs text-muted-foreground mt-0.5 uppercase tracking-wide">{stat.label}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {!auth.user && (
                            <Button size="lg" className="px-10 shadow-amber hover:scale-[1.01] transition-all" asChild>
                                <Link href={route('register')}>Get started free</Link>
                            </Button>
                        )}
                    </div>
                </section>

                {/* Footer */}
                <footer className="border-t border-[--border] bg-[--surface-2] px-6 py-10">
                    <div className="mx-auto max-w-6xl flex flex-col items-center gap-4 md:flex-row md:justify-between">
                        <div className="flex items-center gap-2.5">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[--amber] shrink-0">
                                <Music className="h-3.5 w-3.5 text-white" />
                            </div>
                            <span className="font-sans text-sm font-semibold text-foreground">WavDash</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Precision audio intelligence for serious producers.
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <Link href={route('login')} className="hover:text-foreground transition-colors">Sign in</Link>
                            <Link href={route('register')} className="hover:text-foreground transition-colors">Register</Link>
                        </div>
                    </div>
                </footer>
            </div>
        </>
    );
}
