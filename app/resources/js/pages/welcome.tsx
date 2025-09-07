import { type SharedData } from '@/types';
import { Head, Link, usePage } from '@inertiajs/react';
import { Button } from '@/components/ui/neo/button';
import { BarChart3, Scissors, Gauge, Play, Music, Volume2 } from 'lucide-react';

// Brutalist feature card component
const BrutalistFeatureCard = ({ title, description, color, icon: Icon }: {
  title: string;
  description: string;
  color: string;
  icon: React.ElementType;
}) => (
  <div className={`border-2 border-border shadow-shadow ${color} p-8 hover:shadow-none hover:translate-x-boxShadowX hover:translate-y-boxShadowY transition-all`}>
    <div className="w-16 h-16 bg-main-foreground border-2 border-border flex items-center justify-center mb-6">
      <Icon className="h-8 w-8 text-background" />
    </div>
    <h3 className="font-heading font-black text-xl uppercase tracking-widest text-main-foreground mb-4">
      {title}
    </h3>
    <p className="font-base font-bold text-main-foreground leading-tight">
      {description}
    </p>
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
      backgroundSize: '20px 20px'
    }}
  />
);

export default function BrutalistWelcome() {
    const { auth } = usePage<SharedData>().props;

    return (
        <>
            <Head title="Beat Forge - Destroy Your Audio">
                <meta name="description" content="Beat Forge - The ultimate audio processing platform. Analyze everything, extract stems, dominate the beats." />
            </Head>
            
            <div className="min-h-screen bg-main-foreground text-background">
                {/* Hero Section */}
                <section className="relative h-screen flex items-center justify-center">
                    <GridPattern />
                    
                    {/* Navigation */}
                    <nav className="absolute top-6 right-6 flex items-center gap-4 z-20">
                        {auth.user ? (
                            <Button
                                variant="outline"
                                className="border-background text-background hover:bg-background hover:text-main-foreground font-heading font-black uppercase tracking-wider"
                                asChild
                            >
                                <Link href={route('dashboard')}>DASHBOARD</Link>
                            </Button>
                        ) : (
                            <div className="flex gap-4">
                                <Button
                                    variant="outline"
                                    className="border-background text-background hover:bg-background hover:text-main-foreground font-heading font-black uppercase tracking-wider"
                                    asChild
                                >
                                    <Link href={route('login')}>LOGIN</Link>
                                </Button>
                                <Button
                                    className="bg-chart-3 text-main-foreground hover:bg-chart-1 font-heading font-black uppercase tracking-wider"
                                    asChild
                                >
                                    <Link href={route('register')}>REGISTER</Link>
                                </Button>
                            </div>
                        )}
                    </nav>
                    
                    <div className="text-center space-y-8 z-10 px-6">
                        <div className="mb-8">
                            {/* Logo/Icon */}
                            <div className="w-24 h-24 mx-auto mb-6 bg-chart-1 border-2 border-border shadow-shadow flex items-center justify-center">
                                <Music className="h-12 w-12 text-main-foreground" />
                            </div>
                        </div>
                        
                        <h1 className="text-6xl md:text-8xl font-heading font-black uppercase tracking-widest leading-tight">
                            <span className="block text-chart-1">BEAT</span>
                            <span className="block text-chart-2">FORGE</span>
                        </h1>
                        
                        <p className="text-xl md:text-2xl font-base font-bold uppercase tracking-wider max-w-2xl mx-auto leading-relaxed">
                            DESTROY YOUR AUDIO • ANALYZE EVERYTHING • DOMINATE THE BEATS
                        </p>
                        
                        <div className="flex flex-col md:flex-row gap-4 justify-center items-center mt-12">
                            <Button 
                                size="lg" 
                                className="bg-chart-3 text-main-foreground hover:bg-chart-2 hover:text-background font-heading font-black uppercase tracking-widest px-8 py-4 text-lg"
                                asChild
                            >
                                <Link href={auth.user ? route('uploads.create') : route('register')}>
                                    {auth.user ? 'START UPLOADING' : 'START DESTROYING'}
                                </Link>
                            </Button>
                            
                            <Button 
                                variant="outline" 
                                size="lg"
                                className="border-background text-background hover:bg-background hover:text-main-foreground font-heading font-black uppercase tracking-widest px-8 py-4 text-lg"
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
                <section className="py-20 px-6 bg-background">
                    <div className="max-w-6xl mx-auto">
                        <div className="text-center mb-16">
                            <h2 className="text-4xl md:text-6xl font-heading font-black uppercase tracking-widest text-foreground mb-6">
                                TOOLS OF DESTRUCTION
                            </h2>
                            <p className="text-lg font-base font-bold text-foreground/70 uppercase tracking-wide">
                                UNLEASH THE POWER OF AUDIO PROCESSING
                            </p>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
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
                <section className="py-20 px-6 bg-main-foreground">
                    <div className="max-w-4xl mx-auto text-center">
                        <h2 className="text-3xl md:text-5xl font-heading font-black uppercase tracking-widest text-background mb-8">
                            SEE THE POWER
                        </h2>
                        
                        {/* Mock audio waveform */}
                        <div className="border-2 border-background shadow-shadow bg-background p-8 mb-8">
                            <div className="flex items-center justify-center space-x-1 h-32">
                                {[...Array(40)].map((_, i) => (
                                    <div
                                        key={i}
                                        className="w-2 bg-chart-1 animate-pulse"
                                        style={{
                                            height: `${30 + Math.random() * 70}px`,
                                            animationDelay: `${i * 0.05}s`,
                                            animationDuration: '2s'
                                        }}
                                    />
                                ))}
                            </div>
                            <div className="flex justify-center mt-6">
                                <Button
                                    size="lg"
                                    className="bg-chart-1 text-main-foreground hover:bg-chart-2 w-16 h-16 p-0"
                                >
                                    <Play className="h-8 w-8" />
                                </Button>
                            </div>
                        </div>
                        
                        <p className="text-lg font-base font-bold text-background/80 uppercase tracking-wide mb-8">
                            UPLOAD • ANALYZE • DESTROY • REPEAT
                        </p>
                        
                        {!auth.user && (
                            <Button
                                size="lg"
                                className="bg-chart-3 text-main-foreground hover:bg-chart-1 font-heading font-black uppercase tracking-widest px-12 py-4 text-xl"
                                asChild
                            >
                                <Link href={route('register')}>JOIN THE FORGE</Link>
                            </Button>
                        )}
                    </div>
                </section>

                {/* Footer */}
                <footer className="py-12 px-6 bg-border border-t-2 border-border">
                    <div className="max-w-4xl mx-auto text-center">
                        <div className="flex justify-center items-center mb-6">
                            <div className="w-12 h-12 bg-chart-1 border-2 border-border shadow-shadow flex items-center justify-center mr-4">
                                <Volume2 className="h-6 w-6 text-main-foreground" />
                            </div>
                            <h3 className="text-2xl font-heading font-black uppercase tracking-widest text-foreground">
                                BEAT FORGE
                            </h3>
                        </div>
                        <p className="font-base font-bold text-foreground/70 uppercase tracking-wide text-sm">
                            FORGED WITH BRUTALITY • POWERED BY PASSION • BUILT FOR BEATS
                        </p>
                    </div>
                </footer>
            </div>
        </>
    );
}