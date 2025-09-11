import { Button } from '@/components/ui/neo/button';
import { type SharedData } from '@/types';
import { Head, Link, usePage } from '@inertiajs/react';
import { BarChart3, Gauge, Music, Play, Scissors, Volume2 } from 'lucide-react';

// Brutalist feature card component
const BrutalistFeatureCard = ({
    title,
    description,
    color,
    icon: Icon,
}: {
    title: string;
    description: string;
    color: string;
    icon: React.ElementType;
}) => (
    <div
        className={`border-2 border-border shadow-shadow ${color} p-8 transition-all hover:translate-x-boxShadowX hover:translate-y-boxShadowY hover:shadow-none`}
    >
        <div className="mb-6 flex h-16 w-16 items-center justify-center border-2 border-border bg-main-foreground">
            <Icon className="h-8 w-8 text-background" />
        </div>
        <h3 className="mb-4 font-heading text-xl font-black tracking-widest text-main-foreground uppercase">{title}</h3>
        <p className="leading-tight font-base font-bold text-main-foreground">{description}</p>
    </div>
);

// Grid pattern background component
const GridPattern = () => (
    <div
        className="absolute inset-0 opacity-10"
        style={{
            backgroundImage: `
        linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
      `,
            backgroundSize: '20px 20px',
        }}
    />
);

export default function BrutalistWelcome() {
    const { auth } = usePage<SharedData>().props;

    return (
        <>
            <Head title="Beat Forge - Destroy Your Audio">
                <meta
                    name="description"
                    content="Beat Forge - The ultimate audio processing platform. Analyze everything, extract stems, dominate the beats."
                />
            </Head>

            <div className="min-h-screen bg-main-foreground text-background">
                {/* Hero Section */}
                <section className="relative flex h-screen items-center justify-center">
                    <GridPattern />

                    {/* Navigation */}
                    <nav className="absolute top-6 right-6 z-20 flex items-center gap-4">
                        {auth.user ? (
                            <Button
                                variant="neutral"
                                className="border-background font-heading font-black tracking-wider text-background uppercase hover:bg-background hover:text-main-foreground"
                                asChild
                            >
                                <Link href={route('dashboard')}>DASHBOARD</Link>
                            </Button>
                        ) : (
                            <div className="flex gap-4">
                                <Button
                                    variant="neutral"
                                    className="border-background font-heading font-black tracking-wider text-background uppercase hover:bg-background hover:text-main-foreground"
                                    asChild
                                >
                                    <Link href={route('login')}>LOGIN</Link>
                                </Button>
                                <Button
                                    className="bg-chart-3 font-heading font-black tracking-wider text-main-foreground uppercase hover:bg-chart-1"
                                    asChild
                                >
                                    <Link href={route('register')}>REGISTER</Link>
                                </Button>
                            </div>
                        )}
                    </nav>

                    <div className="z-10 space-y-8 px-6 text-center">
                        <div className="mb-8">
                            {/* Logo/Icon */}
                            <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center border-2 border-border bg-chart-1 shadow-shadow">
                                <Music className="h-12 w-12 text-main-foreground" />
                            </div>
                        </div>

                        <h1 className="font-heading text-6xl leading-tight font-black tracking-widest uppercase md:text-8xl">
                            <span className="block text-chart-1">BEAT</span>
                            <span className="block text-chart-2">FORGE</span>
                        </h1>

                        <p className="mx-auto max-w-2xl text-xl leading-relaxed font-base font-bold tracking-wider uppercase md:text-2xl">
                            DESTROY YOUR AUDIO • ANALYZE EVERYTHING • DOMINATE THE BEATS
                        </p>

                        <div className="mt-12 flex flex-col items-center justify-center gap-4 md:flex-row">
                            <Button
                                size="lg"
                                className="bg-chart-3 px-8 py-4 font-heading text-lg font-black tracking-widest text-main-foreground uppercase hover:bg-chart-2 hover:text-background"
                                asChild
                            >
                                <Link href={auth.user ? route('uploads.create') : route('register')}>
                                    {auth.user ? 'START UPLOADING' : 'START DESTROYING'}
                                </Link>
                            </Button>

                            <Button
                                variant="neutral"
                                size="lg"
                                className="border-background px-8 py-4 font-heading text-lg font-black tracking-widest text-background uppercase hover:bg-background hover:text-main-foreground"
                                asChild
                            >
                                <Link href={auth.user ? route('dashboard') : route('login')}>
                                    {auth.user ? 'GO TO DASHBOARD' : 'ENTER THE FORGE'}
                                </Link>
                            </Button>
                        </div>
                    </div>
                </section>

                {/* Features Grid Section */}
                <section className="bg-background px-6 py-20">
                    <div className="mx-auto max-w-6xl">
                        <div className="mb-16 text-center">
                            <h2 className="mb-6 font-heading text-4xl font-black tracking-widest text-foreground uppercase md:text-6xl">
                                TOOLS OF DESTRUCTION
                            </h2>
                            <p className="text-lg font-base font-bold tracking-wide text-foreground/70 uppercase">
                                UNLEASH THE POWER OF AUDIO PROCESSING
                            </p>
                        </div>

                        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
                            <BrutalistFeatureCard
                                title="AUDIO ANALYSIS"
                                description="RIP APART YOUR TRACKS • FIND THE DNA • DISCOVER THE SECRETS • EXTRACT EVERY DETAIL"
                                color="bg-chart-1"
                                icon={BarChart3}
                            />
                            <BrutalistFeatureCard
                                title="STEM SEPARATION"
                                description="SLICE AND DICE • ISOLATE EVERYTHING • REBUILD FROM CHAOS • TOTAL CONTROL"
                                color="bg-chart-2"
                                icon={Scissors}
                            />
                            <BrutalistFeatureCard
                                title="TEMPO WARFARE"
                                description="SPEED UP • SLOW DOWN • PITCH SHIFT • TIME STRETCH • COMMAND TIME ITSELF"
                                color="bg-chart-4"
                                icon={Gauge}
                            />
                        </div>
                    </div>
                </section>

                {/* Demo Section */}
                <section className="bg-main-foreground px-6 py-20">
                    <div className="mx-auto max-w-4xl text-center">
                        <h2 className="mb-8 font-heading text-3xl font-black tracking-widest text-background uppercase md:text-5xl">SEE THE POWER</h2>

                        {/* Mock audio waveform */}
                        <div className="mb-8 border-2 border-background bg-background p-8 shadow-shadow">
                            <div className="flex h-32 items-center justify-center space-x-1">
                                {[...Array(40)].map((_, i) => (
                                    <div
                                        key={i}
                                        className="w-2 animate-pulse bg-chart-1"
                                        style={{
                                            height: `${30 + Math.random() * 70}px`,
                                            animationDelay: `${i * 0.05}s`,
                                            animationDuration: '2s',
                                        }}
                                    />
                                ))}
                            </div>
                            <div className="mt-6 flex justify-center">
                                <Button size="lg" className="h-16 w-16 bg-chart-1 p-0 text-main-foreground hover:bg-chart-2">
                                    <Play className="h-8 w-8" />
                                </Button>
                            </div>
                        </div>

                        <p className="mb-8 text-lg font-base font-bold tracking-wide text-background/80 uppercase">
                            UPLOAD • ANALYZE • DESTROY • REPEAT
                        </p>

                        {!auth.user && (
                            <Button
                                size="lg"
                                className="bg-chart-3 px-12 py-4 font-heading text-xl font-black tracking-widest text-main-foreground uppercase hover:bg-chart-1"
                                asChild
                            >
                                <Link href={route('register')}>JOIN THE FORGE</Link>
                            </Button>
                        )}
                    </div>
                </section>

                {/* Footer */}
                <footer className="border-t-2 border-border bg-border px-6 py-12">
                    <div className="mx-auto max-w-4xl text-center">
                        <div className="mb-6 flex items-center justify-center">
                            <div className="mr-4 flex h-12 w-12 items-center justify-center border-2 border-border bg-chart-1 shadow-shadow">
                                <Volume2 className="h-6 w-6 text-main-foreground" />
                            </div>
                            <h3 className="font-heading text-2xl font-black tracking-widest text-foreground uppercase">BEAT FORGE</h3>
                        </div>
                        <p className="text-sm font-base font-bold tracking-wide text-foreground/70 uppercase">
                            FORGED WITH BRUTALITY • POWERED BY PASSION • BUILT FOR BEATS
                        </p>
                    </div>
                </footer>
            </div>
        </>
    );
}
