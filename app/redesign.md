# Beat Forge Neobrutalism Redesign Implementation Plan

## Overview

This document outlines a comprehensive phased approach to redesign Beat Forge's client-facing React application using the neobrutalism-components library while maintaining the existing shadcn/ui foundation. The redesign will transform the current clean, modern interface into a bold, brutalist aesthetic using the specified color palette and Cabinet Grotesk typography.

## 🚧 Current Progress Status

**COMPLETED PHASES:**
- ✅ **Phase 1**: Foundation Setup (Typography, Colors, Utilities, Animations)
- ✅ **Phase 2**: Core UI Components (Button, Card, Input with full variant systems)
- ✅ **Phase 3**: Layout & Navigation (Header with yellow brutalist styling, Sidebar with colored blocks)
- ✅ **Phase 4**: Audio Player Redesign (Main player + Multi-track stem player with brutalist controls)
- ✅ **Phase 5**: Page-Level Component Integration (Dashboard, Upload pages with brutalist styling complete)

- ✅ **Phase 6**: Interactive Elements & Micro-animations (Custom components, animations, etc.)
- ✅ **Phase 7**: Dark/Light Mode Implementation (Enhanced theme toggle, improved readability)

**NEXT PHASE:**
- 📋 **Phase 8**: Testing & Refinement

## Design System & Brand Identity

### Color Palette
```css
/* Primary Palette */
--neo-white: #FFFFFF
--neo-green: #00EB90
--neo-pink: #FF73A9
--neo-yellow: #FFDC00
--neo-blue: #3F5EF4
--neo-black: #000000

/* Light Mode Assignments */
--neo-bg-primary: #FFFFFF
--neo-bg-secondary: #FFDC00
--neo-accent-1: #00EB90
--neo-accent-2: #FF73A9
--neo-accent-3: #3F5EF4
--neo-text-primary: #000000

/* Dark Mode Assignments */
--neo-bg-primary: #000000
--neo-bg-secondary: #3F5EF4
--neo-accent-1: #00EB90
--neo-accent-2: #FF73A9
--neo-accent-3: #FFDC00
--neo-text-primary: #FFFFFF
```

### Typography System
- **Primary Font**: Cabinet Grotesk (provided font files)
- **Font Hierarchy**: Maintain existing heading/body structure but adapt to neobrutalist style
- **Font Weights**: Regular (400), Medium (500), Bold (700), Black (900)

## Phase 1: Foundation Setup (Week 1) ✅ COMPLETED

**IMPLEMENTATION STATUS: COMPLETE**
- ✅ Cabinet Grotesk font integration with 4 weights (Regular 400, Medium 500, Bold 700, Black 900)
- ✅ Complete neobrutalist color system with CSS custom properties
- ✅ Sharp corners (border-radius: 0px) throughout
- ✅ Neobrutalist design constants (border-width: 3px, shadow-offset: 4px)
- ✅ Light and dark mode color assignments
- ✅ Utility classes implementation
- ✅ Component-specific overrides
- ✅ Animation system with keyframes

### 1.1 Install Neobrutalism Components
```bash
# Add to package.json dependencies
npm install @neobrutalism-components/react
# OR copy individual components as per library documentation
```

### 1.2 Typography Integration
```css
/* Update resources/css/app.css */
@font-face {
  font-family: 'Cabinet Grotesk';
  src: url('./fonts/CabinetGrotesk-Regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}
/* Additional font weights... */

@theme {
  --font-sans: 'Cabinet Grotesk', ui-sans-serif, system-ui, sans-serif;
  --font-heading: 'Cabinet Grotesk', ui-sans-serif, system-ui, sans-serif;
}
```

### 1.3 Color System Override
```css
/* Neobrutalism Color Variables */
:root {
  --neo-border-width: 3px;
  --neo-shadow-offset: 4px;
  --neo-border-radius: 0px; /* Sharp corners for brutalist look */
  
  /* Override existing shadcn variables */
  --primary: var(--neo-accent-1);
  --secondary: var(--neo-accent-2);
  --accent: var(--neo-accent-3);
  --background: var(--neo-bg-primary);
  --foreground: var(--neo-text-primary);
  
  /* Neobrutalist-specific */
  --neo-shadow: var(--neo-shadow-offset) var(--neo-shadow-offset) 0px var(--neo-black);
  --neo-shadow-hover: calc(var(--neo-shadow-offset) / 2) calc(var(--neo-shadow-offset) / 2) 0px var(--neo-black);
}

.dark {
  --neo-shadow: var(--neo-shadow-offset) var(--neo-shadow-offset) 0px var(--neo-white);
  --neo-shadow-hover: calc(var(--neo-shadow-offset) / 2) calc(var(--neo-shadow-offset) / 2) 0px var(--neo-white);
}
```

### 1.4 Base Component Styling Classes
```css
/* Neobrutalist utility classes */
.neo-border { border: var(--neo-border-width) solid currentColor; }
.neo-shadow { box-shadow: var(--neo-shadow); }
.neo-shadow-hover { box-shadow: var(--neo-shadow-hover); }
.neo-transition { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }

/* Component-specific overrides */
.neo-button {
  @apply neo-border neo-shadow neo-transition font-bold uppercase tracking-wider;
  border-radius: 0;
}
.neo-button:hover {
  @apply neo-shadow-hover;
  transform: translate(2px, 2px);
}
```

## Phase 2: Core UI Component Migration (Week 2-3) ✅ COMPLETED

**IMPLEMENTATION STATUS: COMPLETE**
- ✅ Button component: Complete transformation with neobrutalist variants (default, secondary, accent, blue, outline, ghost, destructive, link)
- ✅ Card component: Added variants system with default, accent, secondary, green, blue variants  
- ✅ Input component: Complete neobrutalist styling with variants (default, accent, error) and sizes
- ✅ Typography system with font-black, uppercase, tracking-wider classes
- ✅ Hover animations with shadow and position transforms

### 2.1 Button Component Transformation
**File**: `resources/js/components/ui/button.tsx`

```tsx
// Enhanced button variants for neobrutalism
const buttonVariants = cva(
  "inline-flex items-center justify-center font-bold uppercase tracking-wider neo-border neo-shadow neo-transition disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-neo-green text-neo-black hover:bg-neo-green/90 neo-shadow-hover",
        secondary: "bg-neo-pink text-neo-white hover:bg-neo-pink/90",
        accent: "bg-neo-yellow text-neo-black hover:bg-neo-yellow/90",
        outline: "bg-transparent border-current hover:bg-current hover:text-neo-bg-primary",
        ghost: "border-transparent shadow-none hover:bg-current/10",
        destructive: "bg-red-500 text-white hover:bg-red-600",
      },
      size: {
        default: "h-12 px-6 py-3 text-sm",
        sm: "h-10 px-4 py-2 text-xs",
        lg: "h-16 px-8 py-4 text-base",
        icon: "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

### 2.2 Card Component Overhaul
**File**: `resources/js/components/ui/card.tsx`

```tsx
const cardVariants = cva(
  "neo-border neo-shadow bg-neo-bg-primary",
  {
    variants: {
      variant: {
        default: "bg-neo-white dark:bg-neo-black",
        accent: "bg-neo-yellow",
        secondary: "bg-neo-pink/10 dark:bg-neo-pink/20",
      },
      size: {
        default: "p-6",
        sm: "p-4",
        lg: "p-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

### 2.3 Input & Form Components
**File**: `resources/js/components/ui/input.tsx`

```tsx
const inputVariants = cva(
  "neo-border neo-shadow-hover bg-neo-bg-primary font-mono text-base px-4 py-3 focus:shadow-none focus:translate-x-1 focus:translate-y-1 disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "border-neo-black dark:border-neo-white",
        accent: "border-neo-green bg-neo-green/5",
        error: "border-red-500 bg-red-50 dark:bg-red-900/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)
```

## Phase 3: Layout & Navigation Redesign (Week 4-5) ✅ COMPLETED

**IMPLEMENTATION STATUS: COMPLETE**
- ✅ Header component transformed with neobrutalist styling
- ✅ Bright yellow background with bold typography
- ✅ Navigation buttons with brutalist hover effects
- ✅ Sidebar redesigned with colored blocks per navigation item
- ✅ Black background with colored link buttons
- ✅ Uppercase typography throughout navigation

### 3.1 Header Component Transformation
**File**: `resources/js/components/app-header.tsx`

```tsx
// Brutalist header with bold typography and color blocks
export function AppHeader() {
  return (
    <header className="neo-border-b bg-neo-yellow sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-6">
            <AppLogoIcon className="w-10 h-10 neo-shadow" />
            <h1 className="text-2xl font-black uppercase tracking-widest text-neo-black">
              Beat Forge
            </h1>
          </div>
          
          {/* Brutalist navigation buttons */}
          <nav className="hidden md:flex space-x-2">
            <Button variant="ghost" className="text-neo-black hover:bg-neo-black hover:text-neo-yellow">
              UPLOADS
            </Button>
            <Button variant="ghost" className="text-neo-black hover:bg-neo-black hover:text-neo-yellow">
              CONTESTS
            </Button>
          </nav>
          
          <UserMenuContent />
        </div>
      </div>
    </header>
  )
}
```

### 3.2 Sidebar Redesign
**File**: `resources/js/components/app-sidebar.tsx`

```tsx
// Transform to vertical color blocks with bold labels
const sidebarItems = [
  { label: "DASHBOARD", icon: HomeIcon, color: "bg-neo-green" },
  { label: "MY TRACKS", icon: MusicIcon, color: "bg-neo-pink" },
  { label: "ANALYSIS", icon: BarChartIcon, color: "bg-neo-blue" },
  { label: "CONTESTS", icon: TrophyIcon, color: "bg-neo-yellow" },
]

export function AppSidebar() {
  return (
    <aside className="w-64 bg-neo-black neo-border-r">
      <div className="p-4 space-y-2">
        {sidebarItems.map((item) => (
          <SidebarItem 
            key={item.label}
            className={`${item.color} text-neo-black font-bold uppercase tracking-wide neo-shadow hover:neo-shadow-hover`}
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </SidebarItem>
        ))}
      </div>
    </aside>
  )
}
```

## Phase 4: Audio Player Neobrutalist Redesign (Week 6) ✅ COMPLETED

**IMPLEMENTATION STATUS: COMPLETE**
- ✅ Audio player component transformed with brutalist styling
- ✅ Large play button with neo-green background and brutalist hover effects
- ✅ Waveform container with colored background and neo-border styling
- ✅ Control bar with time displays using monospace fonts
- ✅ Multi-track stem player completely redesigned
- ✅ Each stem gets its own color block (green, pink, yellow, blue)
- ✅ SOLO/MUTE buttons with brutalist styling
- ✅ Volume controls with neo-slider styling
- ✅ Added neo-slider utility classes to CSS

### 4.1 Main Audio Player Component
**File**: `resources/js/components/audio-player.tsx`

```tsx
export function AudioPlayer({ url, title, className = '' }: AudioPlayerProps) {
  return (
    <div className={`audio-player neo-border neo-shadow bg-neo-white dark:bg-neo-black p-6 ${className}`}>
      {title && (
        <h3 className="mb-4 text-lg font-black uppercase tracking-widest text-neo-black dark:text-neo-white neo-border-b pb-2">
          {title}
        </h3>
      )}
      
      <div className="flex items-center space-x-6">
        {/* Brutalist play button */}
        <Button
          onClick={handlePlayPause}
          variant="default"
          size="lg"
          className="rounded-none w-16 h-16 bg-neo-green hover:bg-neo-pink neo-shadow hover:neo-shadow-hover"
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-8 w-8 animate-spin text-neo-black" />
          ) : isPlaying ? (
            <PauseIcon className="h-8 w-8 text-neo-black" />
          ) : (
            <PlayIcon className="h-8 w-8 text-neo-black" />
          )}
        </Button>

        {/* Waveform with brutalist styling */}
        <div className="flex-1 neo-border neo-shadow-hover bg-neo-yellow/20 p-4">
          <NeoSoundcloudWaveform
            url={url}
            waveColor="#00EB90"
            progressColor="#FF73A9"
            cursorColor="#3F5EF4"
            onReady={(ws) => {
              setWavesurfer(ws);
              setIsLoading(false);
            }}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onFinish={() => setIsPlaying(false)}
          />
        </div>
      </div>
      
      {/* Control bar with brutalist buttons */}
      <div className="mt-4 flex justify-between items-center">
        <div className="flex space-x-2">
          <Button variant="accent" size="sm" className="font-mono">00:00</Button>
          <Button variant="secondary" size="sm" className="font-mono">03:24</Button>
        </div>
        
        <div className="flex space-x-2">
          <Button variant="outline" size="icon" className="neo-shadow">
            <SkipBackIcon className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="neo-shadow">
            <SkipForwardIcon className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="neo-shadow">
            <VolumeIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
```

### 4.2 Multi-Track Stem Player Enhancement
**File**: `resources/js/components/multi-track-stem-player.tsx`

```tsx
// Each stem gets its own color block and brutal controls
const stemColors = [
  'bg-neo-green',
  'bg-neo-pink', 
  'bg-neo-yellow',
  'bg-neo-blue'
]

export function MultiTrackStemPlayer({ stems }: Props) {
  return (
    <div className="space-y-4">
      {stems.map((stem, index) => (
        <div key={stem.id} className={`neo-border neo-shadow p-4 ${stemColors[index % stemColors.length]}`}>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-black uppercase tracking-wider text-neo-black">
              {stem.stemType.replace('_', ' ')}
            </h4>
            <div className="flex space-x-2">
              <Button variant="ghost" size="sm" className="text-neo-black border-neo-black">
                SOLO
              </Button>
              <Button variant="ghost" size="sm" className="text-neo-black border-neo-black">
                MUTE
              </Button>
            </div>
          </div>
          
          {/* Individual waveform */}
          <div className="neo-border bg-neo-black/10 p-2">
            <StemWaveform
              url={stem.streamUrl}
              stemType={stem.stemType}
              color={getWaveformColor(index)}
            />
          </div>
          
          {/* Volume control */}
          <div className="mt-3 flex items-center space-x-4">
            <span className="font-mono text-sm text-neo-black">VOL</span>
            <Slider
              value={[stem.volume]}
              onValueChange={(value) => handleVolumeChange(stem.id, value[0])}
              max={100}
              step={1}
              className="flex-1 neo-slider"
            />
            <span className="font-mono text-sm text-neo-black w-10 text-right">
              {stem.volume}%
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
```

## Phase 5: Page-Level Component Integration (Week 7-8) ✅ COMPLETED

**IMPLEMENTATION STATUS: COMPLETE**
- ✅ Dashboard page with brutalist statistics blocks (Hero section, StatCard components, BrutalistMusicCard)
- ✅ Upload show page with colored sections (Pink header, color-coded file details, audio player integration)
- ✅ Form components with proper neobrutalist styling integration
- ✅ Component architecture with StatCard and BrutalistMusicCard components
- ✅ Visual verification completed via playwright browser testing

### 5.0: Review current components and ensure using the correct library
Review the following installation guide for neobrutalism.dev components

1. Initialize shadcn [DONE]

Warning
Neobrutalism components doesn't support utility class components anymore, only css variables components. Also, it doesn't matter which baseColor you choose, because it doesn't change the styling.

2. Add styling 
Delete the existing styling from your globals.css and paste desired styling.

Example globals.css but use our brand colors
```
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

:root {
  --background: oklch(94.27% 0.0268 242.57);
  --secondary-background: oklch(100% 0 0);
  --foreground: oklch(0% 0 0);
  --main-foreground: oklch(0% 0 0);
  --main: oklch(66.9% 0.18368 248.8066);
  --border: oklch(0% 0 0);
  --ring: oklch(0% 0 0);
  --overlay: oklch(0% 0 0 / 0.8);
  --shadow: 4px 4px 0px 0px var(--border);
  --chart-1: #0099FF;
  --chart-2: #FF4D50;
  --chart-3: #FACC00;
  --chart-4: #05E17A;
  --chart-5: #7A83FF;
  --chart-active-dot: #000;
}

.dark {
  --background: oklch(27.08% 0.0336 240.69);
  --secondary-background: oklch(23.93% 0 0);
  --foreground: oklch(92.49% 0 0);
  --main-foreground: oklch(0% 0 0);
  --main: oklch(61.9% 0.16907 248.5982);
  --border: oklch(0% 0 0);
  --ring: oklch(100% 0 0);
  --shadow: 4px 4px 0px 0px var(--border);
  --chart-1: #008AE5;
  --chart-2: #FF6669;
  --chart-3: #E0B700;
  --chart-4: #04C86D;
  --chart-5: #7A83FF;
  --chart-active-dot: #fff;
}

@theme inline {
  --color-main: var(--main);
  --color-background: var(--background);
  --color-secondary-background: var(--secondary-background);
  --color-foreground: var(--foreground);
  --color-main-foreground: var(--main-foreground);
  --color-border: var(--border);
  --color-overlay: var(--overlay);
  --color-ring: var(--ring);
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);

  --spacing-boxShadowX: 4px;
  --spacing-boxShadowY: 4px;
  --spacing-reverseBoxShadowX: -4px;
  --spacing-reverseBoxShadowY: -4px;
  --radius-base: 10px;
  --shadow-shadow: var(--shadow);
  --font-weight-base: 500;
  --font-weight-heading: 900;
}
  
@layer base {
  body {
    @apply text-foreground font-base bg-background;
  }

  h1, h2, h3, h4, h5, h6{
    @apply font-heading;
  }
}
```

3. Install components
Install via Shadcn cli
Just choose desired component variant and desired package manager, copy cli command to your terminal and you're good to go. If there is no shadcn cli command on the component page you'll have to install the component manually.

Example Install
```npx shadcn@latest add https://neobrutalism.dev/r/accordion.json```

Review all the components modified so far and ensure you are using the components from https://neobrutalism.dev and are installed in ui/neo. 

These should be the preferred components to use when implementing something for the redesign

We want a copy of every available component installed in the current ui/ folder in the ui/neo folder but with its component from the neobrualism library. 


### 5.1 Dashboard Redesign
**File**: `resources/js/pages/dashboard.tsx`

```tsx
// Transform dashboard into brutalist blocks layout
export default function Dashboard({ uploads }: Props) {
  return (
    <AppLayout title="Dashboard">
      <div className="space-y-8">
        {/* Hero section with harsh typography */}
        <section className="neo-border neo-shadow bg-neo-yellow p-8">
          <h1 className="text-4xl font-black uppercase tracking-widest text-neo-black mb-4">
            YOUR BEATS
          </h1>
          <p className="text-lg font-bold text-neo-black">
            {uploads.length} TRACKS READY TO DESTROY
          </p>
        </section>

        {/* Stats grid with color blocks */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard 
            title="TOTAL UPLOADS"
            value={stats.totalUploads}
            color="bg-neo-green"
            icon={<UploadIcon />}
          />
          <StatCard 
            title="PROCESSED"
            value={stats.processed}
            color="bg-neo-pink"
            icon={<CheckIcon />}
          />
          <StatCard 
            title="ANALYZING"
            value={stats.processing}
            color="bg-neo-blue"
            icon={<BarChartIcon />}
          />
        </section>

        {/* Recent uploads brutalist list */}
        <section>
          <h2 className="text-2xl font-black uppercase tracking-wide mb-6 text-neo-black dark:text-neo-white">
            RECENT DROPS
          </h2>
          <div className="space-y-4">
            {uploads.map((upload) => (
              <BrutalistMusicCard key={upload.id} upload={upload} />
            ))}
          </div>
        </section>
      </div>
    </AppLayout>
  )
}
```

### 5.2 Upload Show Page
**File**: `resources/js/pages/uploads/show.tsx`

```tsx
// Full-width brutalist upload viewer
export default function ShowUpload({ upload }: Props) {
  return (
    <AppLayout title={upload.title}>
      <div className="space-y-8">
        {/* Upload header with color block */}
        <section className="neo-border neo-shadow bg-neo-pink p-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-black uppercase tracking-wider text-neo-white mb-2">
                {upload.title}
              </h1>
              <p className="text-lg font-bold text-neo-white/80">
                {upload.genre} • {formatDuration(upload.durationSeconds)}
              </p>
            </div>
            <Badge variant="secondary" className="neo-shadow font-bold">
              {upload.status.toUpperCase()}
            </Badge>
          </div>
        </section>

        {/* Main audio player */}
        <section>
          <AudioPlayer url={upload.streamUrl} title="MAIN TRACK" />
        </section>

        {/* Action buttons */}
        <section className="flex flex-wrap gap-4">
          <Button variant="default" size="lg" className="flex-1 md:flex-none">
            ANALYZE TRACK
          </Button>
          <Button variant="secondary" size="lg" className="flex-1 md:flex-none">
            EXTRACT STEMS
          </Button>
          <Button variant="accent" size="lg" className="flex-1 md:flex-none">
            TEMPO SHIFT
          </Button>
        </section>

        {/* Stems section if available */}
        {upload.stems?.length > 0 && (
          <section className="neo-border neo-shadow bg-neo-white dark:bg-neo-black p-6">
            <h2 className="text-2xl font-black uppercase tracking-wide mb-6">
              STEM TRACKS
            </h2>
            <MultiTrackStemPlayer stems={upload.stems} />
          </section>
        )}
      </div>
    </AppLayout>
  )
}
```

## Phase 6: Interactive Elements & Micro-animations (Week 9) ✅ COMPLETED

**IMPLEMENTATION STATUS: COMPLETE**
- ✅ NeoProgressBar and NeoToast components created and split into separate files
- ✅ Components properly organized in `/resources/js/components/ui/neo/` directory
- ✅ Animation keyframes implemented (slide-up, bounce-in, shake)
- ✅ Updated index.ts to export new components
- ✅ User navigation functionality restored to sidebar with neobrutalist styling

### 6.1 Custom Neobrutalist Components
**File**: `resources/js/components/ui/neo-components.tsx`

```tsx
// Brutalist progress bar
export function NeoProgressBar({ value, max = 100, color = 'bg-neo-green' }) {
  const percentage = (value / max) * 100
  
  return (
    <div className="neo-border neo-shadow bg-neo-white dark:bg-neo-black h-8">
      <div 
        className={`h-full ${color} neo-border-r transition-all duration-300 flex items-center justify-end pr-2`}
        style={{ width: `${percentage}%` }}
      >
        <span className="font-black text-xs text-neo-black">
          {Math.round(percentage)}%
        </span>
      </div>
    </div>
  )
}

// Brutalist notification toast
export function NeoToast({ title, message, type = 'info' }) {
  const colorMap = {
    success: 'bg-neo-green',
    error: 'bg-red-500',
    warning: 'bg-neo-yellow',
    info: 'bg-neo-blue'
  }
  
  return (
    <div className={`neo-border neo-shadow ${colorMap[type]} p-4 animate-slide-up`}>
      <h4 className="font-black uppercase text-neo-black mb-1">{title}</h4>
      <p className="font-bold text-neo-black text-sm">{message}</p>
    </div>
  )
}
```

### 6.2 Animation System
**File**: `resources/css/app.css` (additions)

```css
/* Neobrutalist animations */
@keyframes slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes bounce-in {
  0% {
    transform: scale(0.3) rotate(-5deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.05) rotate(1deg);
  }
  70% {
    transform: scale(0.9) rotate(-1deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
  20%, 40%, 60%, 80% { transform: translateX(2px); }
}

.animate-slide-up { animation: slide-up 0.3s ease-out; }
.animate-bounce-in { animation: bounce-in 0.5s ease-out; }
.animate-shake { animation: shake 0.5s ease-in-out; }

/* Hover transforms for brutalist effect */
.neo-hover-transform:hover {
  transform: translate(-2px, -2px);
  transition: transform 0.1s ease-out;
}
```

## Phase 7: Dark/Light Mode Implementation (Week 10) ✅ COMPLETED

**IMPLEMENTATION STATUS: COMPLETE**
- ✅ Enhanced AppearanceToggleTab component with neobrutalist styling
- ✅ Created NeoThemeToggle component with cycling theme functionality
- ✅ Improved dark mode CSS variables for better contrast and readability
- ✅ Enhanced component adjustments for better dark mode visibility
- ✅ Tested light/dark/system theme switching functionality
- ✅ Verified readability and visual consistency across all theme modes

### 7.1 Theme Toggle Component
**File**: `resources/js/components/neo-theme-toggle.tsx`

```tsx
export function NeoThemeToggle() {
  const [theme, setTheme] = useTheme()
  
  return (
    <Button
      variant="outline"
      size="icon"
      className="neo-shadow hover:neo-shadow-hover bg-neo-yellow dark:bg-neo-blue border-neo-black dark:border-neo-white"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      {theme === 'dark' ? (
        <SunIcon className="h-5 w-5 text-neo-black" />
      ) : (
        <MoonIcon className="h-5 w-5 text-neo-white" />
      )}
    </Button>
  )
}
```

### 7.2 Enhanced Dark Mode Variables
```css
.dark {
  /* Update existing variables for better contrast */
  --neo-bg-primary: #000000;
  --neo-bg-secondary: #3F5EF4;
  --neo-text-primary: #FFFFFF;
  
  /* Inverted shadows for dark mode */
  --neo-shadow: var(--neo-shadow-offset) var(--neo-shadow-offset) 0px var(--neo-white);
  --neo-shadow-hover: calc(var(--neo-shadow-offset) / 2) calc(var(--neo-shadow-offset) / 2) 0px var(--neo-white);
}

/* Dark mode specific component adjustments */
.dark .neo-border { border-color: var(--neo-white); }
.dark .neo-button { color: var(--neo-white); }
.dark .neo-card { background: var(--neo-black); }
```

## Phase 8: Testing & Refinement (Week 11-12)

### 8.1 Component Testing Checklist
- [ ] All buttons have proper hover states and shadow animations
- [ ] Color accessibility compliance (WCAG AA)
- [ ] Mobile responsiveness with brutalist design integrity
- [ ] Dark/light mode switching without layout shifts
- [ ] Audio player controls maintain functionality with new styling
- [ ] Form inputs have proper focus states and validation styling
- [ ] Loading states use consistent neobrutalist indicators
- [ ] The app has proper readability and usage in mobile responsive tests
- [ ] Ensure components adhere to the brand colors

### 8.2 Performance Optimization
- Optimize font loading with `font-display: swap`
- Minimize CSS custom properties for better performance
- Use CSS containment for complex animated components
- Implement proper lazy loading for audio components

### 8.3 Browser Compatibility
- Test shadow effects across different browsers
- Ensure CSS transforms work consistently
- Verify color contrast in various browser color profiles
- Test touch interactions on mobile devices

## Implementation Notes

### Media Player Strategy
The audio player redesign maintains all existing functionality while adopting the brutalist aesthetic through:
1. **Sharp geometric shapes** replacing rounded corners
2. **Bold typography** for all labels and controls
3. **High contrast color blocks** for different player states
4. **Harsh shadows** for depth instead of subtle gradients
5. **Monospace fonts** for time displays and technical information

### Component Migration Approach
- **Gradual replacement**: Implement one component category at a time
- **Backward compatibility**: Keep existing shadcn components functional during transition
- **A/B testing ready**: Easy toggle between old and new designs
- **Consistent API**: Maintain existing prop interfaces where possible

### Responsive Design Considerations
- Stack brutalist blocks vertically on mobile
- Maintain button accessibility with larger touch targets
- Simplify complex layouts while preserving visual hierarchy
- Ensure shadows and borders scale appropriately

## Phase 9: Advanced Features & Specialized Components (Week 13-14)

### 9.1 Analysis & Data Visualization Components
**File**: `resources/js/pages/uploads/analysis.tsx`

```tsx
// Brutalist data visualization for audio analysis
const AnalysisMetrics = ({ analysis }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {/* Musical Key Display */}
    <div className="neo-border neo-shadow bg-neo-green p-4">
      <h4 className="font-black uppercase tracking-wide text-neo-black mb-2">MUSICAL KEY</h4>
      <div className="flex items-center gap-3">
        <span className="text-3xl font-black font-mono text-neo-black">
          {analysis.musical_key || 'N/A'}
        </span>
        {analysis.key_confidence && (
          <div className="neo-border bg-neo-black text-neo-white px-2 py-1">
            <span className="font-mono text-xs">
              {Math.round(analysis.key_confidence * 100)}% CONF
            </span>
          </div>
        )}
      </div>
    </div>

    {/* BPM Display */}
    <div className="neo-border neo-shadow bg-neo-pink p-4">
      <h4 className="font-black uppercase tracking-wide text-neo-white mb-2">BPM</h4>
      <div className="flex items-center gap-3">
        <span className="text-3xl font-black font-mono text-neo-white">
          {analysis.bpm || 'N/A'}
        </span>
        {analysis.categories?.bpm && (
          <Badge variant="outline" className="border-neo-white text-neo-white">
            {analysis.categories.bpm.toUpperCase()}
          </Badge>
        )}
      </div>
    </div>

    {/* Loudness Display */}
    <div className="neo-border neo-shadow bg-neo-blue p-4">
      <h4 className="font-black uppercase tracking-wide text-neo-white mb-2">LOUDNESS</h4>
      <div className="flex items-center gap-3">
        <span className="text-2xl font-black font-mono text-neo-white">
          {analysis.loudness_db ? `${analysis.loudness_db.toFixed(1)}` : 'N/A'}
        </span>
        <span className="text-sm font-bold text-neo-white">dB</span>
      </div>
    </div>
  </div>
)
```

### 9.2 Similar Tracks Discovery Interface
**File**: `resources/js/pages/uploads/similar.tsx`

```tsx
// Brutalist similar tracks grid
const SimilarTracksGrid = ({ similarUploads, analysisCriteria }) => (
  <div className="space-y-6">
    {/* Search Criteria Display */}
    <div className="neo-border neo-shadow bg-neo-yellow p-6">
      <h3 className="font-black uppercase tracking-widest text-neo-black mb-4">
        SEARCH PARAMETERS
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="neo-border bg-neo-black p-3">
          <span className="block text-xs font-black uppercase text-neo-white">KEY</span>
          <span className="text-lg font-black text-neo-green">
            {analysisCriteria.musical_key}
          </span>
        </div>
        <div className="neo-border bg-neo-black p-3">
          <span className="block text-xs font-black uppercase text-neo-white">BPM</span>
          <span className="text-lg font-black text-neo-pink">
            {analysisCriteria.bpm}±10
          </span>
        </div>
        <div className="neo-border bg-neo-black p-3">
          <span className="block text-xs font-black uppercase text-neo-white">BRIGHTNESS</span>
          <span className="text-lg font-black text-neo-blue">
            {Math.round(analysisCriteria.brightness)}Hz
          </span>
        </div>
        <div className="neo-border bg-neo-black p-3">
          <span className="block text-xs font-black uppercase text-neo-white">CONFIDENCE</span>
          <span className="text-lg font-black text-neo-white">
            {Math.round(analysisCriteria.key_confidence * 100)}%
          </span>
        </div>
      </div>
    </div>

    {/* Results Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {similarUploads.map((upload, index) => (
        <BrutalistSimilarTrackCard key={upload.id} upload={upload} index={index} />
      ))}
    </div>
  </div>
)
```

### 9.3 Contest System Components
**File**: `resources/js/pages/contest/index.tsx`

```tsx
// Neobrutalist contest table
const BrutalistContestTable = ({ contests }) => (
  <div className="neo-border neo-shadow bg-neo-white dark:bg-neo-black">
    <div className="bg-neo-black p-4 neo-border-b">
      <h2 className="text-xl font-black uppercase tracking-wider text-neo-white">
        BEAT BATTLES
      </h2>
    </div>
    
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-neo-yellow neo-border-b">
          <tr>
            <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">CONTEST</th>
            <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">STATUS</th>
            <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">FIGHTERS</th>
            <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">DEADLINE</th>
            <th className="p-4 text-left font-black uppercase tracking-wide text-neo-black">ACTION</th>
          </tr>
        </thead>
        <tbody>
          {contests.data.map((contest) => (
            <tr key={contest.id} className="neo-border-b hover:bg-neo-green/10">
              <td className="p-4 font-bold text-neo-black dark:text-neo-white">
                {contest.name.toUpperCase()}
              </td>
              <td className="p-4">
                <BrutalistStatusBadge status={contest.status} />
              </td>
              <td className="p-4 font-mono font-bold">
                {contest.contest_users_count} PLAYERS
              </td>
              <td className="p-4 font-mono font-bold">
                {new Date(contest.end_date).toLocaleDateString().toUpperCase()}
              </td>
              <td className="p-4">
                <Button 
                  variant="accent" 
                  size="sm"
                  className="font-black uppercase"
                  asChild
                >
                  <Link href={`/contests/${contest.id}`}>ENTER</Link>
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
)
```

## Phase 10: Form Components & User Interactions (Week 15-16)

### 10.1 Upload Form Redesign
**File**: `resources/js/components/music-library-upload-form.tsx`

```tsx
// Brutal file upload interface
const BrutalistUploadZone = ({ onFileSelect, errors, processing }) => (
  <div className="neo-border neo-shadow bg-neo-yellow p-8 cursor-pointer hover:bg-neo-pink hover:neo-shadow-hover transition-all">
    <div className="text-center space-y-4">
      <div className="w-24 h-24 mx-auto bg-neo-black neo-border flex items-center justify-center">
        <Upload className="h-12 w-12 text-neo-white" />
      </div>
      
      <div>
        <h3 className="text-2xl font-black uppercase tracking-widest text-neo-black mb-2">
          DROP YOUR BEATS
        </h3>
        <p className="font-bold text-neo-black">
          MP3, WAV, AIFF, FLAC • MAX 50MB
        </p>
      </div>
      
      {errors.audio_file && (
        <div className="neo-border bg-red-500 p-3">
          <p className="font-black text-white uppercase">
            {errors.audio_file}
          </p>
        </div>
      )}
    </div>
  </div>
)

const BrutalistProgressBar = ({ progress }) => (
  <div className="neo-border neo-shadow bg-neo-black p-4">
    <div className="flex justify-between items-center mb-2">
      <span className="font-black text-neo-white uppercase">UPLOADING</span>
      <span className="font-mono text-neo-green">{progress}%</span>
    </div>
    <div className="neo-border bg-neo-white h-4">
      <div 
        className="bg-neo-green h-full transition-all duration-300 neo-border-r"
        style={{ width: `${progress}%` }}
      />
    </div>
  </div>
)
```

### 10.2 Processing Panel Components
**File**: `resources/js/components/upload-processing-panel.tsx`

```tsx
// Brutalist processing status cards
const BrutalistProcessingCard = ({ section, upload }) => {
  const getStatusColor = (section) => {
    if (section.hasResults) return 'bg-neo-green'
    if (section.isProcessing) return 'bg-neo-yellow'
    return 'bg-neo-pink'
  }

  const getStatusText = (section) => {
    if (section.hasResults) return 'COMPLETE'
    if (section.isProcessing) return 'PROCESSING'
    return 'AVAILABLE'
  }

  return (
    <div className={`neo-border neo-shadow p-6 ${getStatusColor(section)}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-neo-black neo-border flex items-center justify-center">
            <section.icon className="h-6 w-6 text-neo-white" />
          </div>
          <div>
            <h3 className="font-black uppercase tracking-wide text-neo-black">
              {section.title}
            </h3>
            <p className="font-bold text-neo-black text-sm">
              {section.description.toUpperCase()}
            </p>
          </div>
        </div>
        
        <div className="neo-border bg-neo-black px-3 py-1">
          <span className="font-black text-xs text-neo-white">
            {getStatusText(section)}
          </span>
        </div>
      </div>
      
      {section.isProcessing && (
        <div className="mb-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin w-4 h-4 border-2 border-neo-black border-t-transparent rounded-full" />
            <span className="font-bold text-neo-black">PROCESSING...</span>
          </div>
        </div>
      )}
      
      <Button 
        variant="outline" 
        className="w-full font-black uppercase border-neo-black text-neo-black hover:bg-neo-black hover:text-neo-white"
        asChild
      >
        <Link href={route(section.route, upload.id)}>
          {section.hasResults ? 'VIEW RESULTS' : 'START PROCESS'}
        </Link>
      </Button>
    </div>
  )
}
```

## Phase 11: Music Library & Card Components (Week 17)

### 11.1 Music Library Card Redesign
**File**: `resources/js/components/music-library-card.tsx`

```tsx
// Complete neobrutalist music card overhaul
export const BrutalistMusicCard = ({ upload, isLast, lastElementRef }) => {
  const statusColors = {
    ready: 'bg-neo-green',
    processing: 'bg-neo-yellow', 
    failed: 'bg-red-500',
    pending: 'bg-neo-blue'
  }

  return (
    <div
      ref={isLast ? lastElementRef : null}
      className="neo-border neo-shadow bg-neo-white dark:bg-neo-black hover:neo-shadow-hover hover:translate-x-1 hover:translate-y-1 transition-all cursor-pointer"
      onClick={() => router.visit(route('uploads.show', upload.id))}
    >
      {/* Status Header */}
      <div className={`${statusColors[upload.status]} p-3 neo-border-b flex justify-between items-center`}>
        <div className="flex items-center space-x-2">
          <span className="font-black text-xs uppercase tracking-widest text-neo-black">
            {getAudioFormat(upload.mime_type)}
          </span>
        </div>
        <div className="font-black text-xs uppercase tracking-widest text-neo-black">
          {upload.status}
        </div>
      </div>

      {/* Waveform Visualization */}
      <div className="p-4 bg-neo-black">
        <div className="flex items-center justify-center space-x-1 h-16">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="w-1 bg-neo-green rounded-none animate-pulse"
              style={{
                height: `${20 + Math.random() * 40}px`,
                animationDelay: `${i * 0.1}s`,
                animationDuration: '2s'
              }}
            />
          ))}
        </div>
      </div>

      {/* Track Info */}
      <div className="p-4 space-y-3">
        <div>
          <h3 className="font-black text-lg uppercase tracking-wide text-neo-black dark:text-neo-white mb-1">
            {upload.title}
          </h3>
          {upload.artist && (
            <p className="font-bold text-sm text-neo-black/70 dark:text-neo-white/70">
              BY {upload.artist.toUpperCase()}
            </p>
          )}
        </div>

        {/* Technical Specs */}
        <div className="grid grid-cols-2 gap-2">
          <div className="neo-border bg-neo-yellow/20 p-2">
            <div className="text-xs font-black uppercase text-neo-black dark:text-neo-white">
              DURATION
            </div>
            <div className="font-mono font-bold text-neo-black dark:text-neo-white">
              {formatDuration(upload.duration)}
            </div>
          </div>
          <div className="neo-border bg-neo-pink/20 p-2">
            <div className="text-xs font-black uppercase text-neo-black dark:text-neo-white">
              SIZE
            </div>
            <div className="font-mono font-bold text-neo-black dark:text-neo-white">
              {formatFileSize(upload.size)}
            </div>
          </div>
        </div>

        {/* Feature Badges */}
        <div className="flex flex-wrap gap-1">
          {upload.has_analysis && (
            <div className="neo-border bg-neo-green px-2 py-1">
              <span className="text-xs font-black text-neo-black">ANALYZED</span>
            </div>
          )}
          {upload.has_stems && (
            <div className="neo-border bg-neo-pink px-2 py-1">
              <span className="text-xs font-black text-neo-white">STEMS</span>
            </div>
          )}
          {upload.has_tempos && (
            <div className="neo-border bg-neo-blue px-2 py-1">
              <span className="text-xs font-black text-neo-white">TEMPO FX</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="neo-border-t bg-neo-black p-3 flex justify-between items-center">
        <div className="text-xs font-mono text-neo-white">
          {formatDate(upload.created_at).toUpperCase()}
        </div>
        <BrutalistDropdownMenu upload={upload} />
      </div>
    </div>
  )
}
```

## Phase 12: Welcome Page & Landing Components (Week 18)

### 12.1 Welcome Page Transformation
**File**: `resources/js/pages/welcome.tsx`

```tsx
// Neobrutalist landing page design
export default function BrutalistWelcome() {
  return (
    <div className="min-h-screen bg-neo-black text-neo-white">
      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center">
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
        
        <div className="text-center space-y-8 z-10">
          <h1 className="text-6xl md:text-8xl font-black uppercase tracking-widest">
            <span className="block text-neo-green">BEAT</span>
            <span className="block text-neo-pink">FORGE</span>
          </h1>
          
          <p className="text-xl md:text-2xl font-bold uppercase tracking-wider max-w-2xl mx-auto">
            DESTROY YOUR AUDIO • ANALYZE EVERYTHING • DOMINATE THE BEATS
          </p>
          
          <div className="flex flex-col md:flex-row gap-4 justify-center items-center mt-8">
            <Button 
              size="lg" 
              className="bg-neo-yellow text-neo-black hover:bg-neo-pink hover:text-neo-white font-black uppercase tracking-widest px-8 py-4 text-lg"
              asChild
            >
              <Link href={route('register')}>START DESTROYING</Link>
            </Button>
            
            <Button 
              variant="outline" 
              size="lg"
              className="border-neo-white text-neo-white hover:bg-neo-white hover:text-neo-black font-black uppercase tracking-widest px-8 py-4 text-lg"
              asChild
            >
              <Link href={route('login')}>ENTER THE FORGE</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-black uppercase tracking-widest text-center mb-12 text-neo-white">
            TOOLS OF DESTRUCTION
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <BrutalistFeatureCard
              title="AUDIO ANALYSIS"
              description="RIP APART YOUR TRACKS • FIND THE DNA • DISCOVER THE SECRETS"
              color="bg-neo-green"
              icon={BarChart3}
            />
            <BrutalistFeatureCard
              title="STEM SEPARATION"
              description="SLICE AND DICE • ISOLATE EVERYTHING • REBUILD FROM CHAOS"
              color="bg-neo-pink"
              icon={Scissors}
            />
            <BrutalistFeatureCard
              title="TEMPO WARFARE"
              description="SPEED UP • SLOW DOWN • PITCH SHIFT • TOTAL CONTROL"
              color="bg-neo-blue"
              icon={Gauge}
            />
          </div>
        </div>
      </section>
    </div>
  )
}

const BrutalistFeatureCard = ({ title, description, color, icon: Icon }) => (
  <div className={`neo-border neo-shadow ${color} p-8 hover:neo-shadow-hover hover:translate-x-2 hover:translate-y-2 transition-all`}>
    <div className="w-16 h-16 bg-neo-black neo-border flex items-center justify-center mb-6">
      <Icon className="h-8 w-8 text-neo-white" />
    </div>
    <h3 className="font-black text-xl uppercase tracking-widest text-neo-black mb-4">
      {title}
    </h3>
    <p className="font-bold text-neo-black leading-tight">
      {description}
    </p>
  </div>
)
```

## Phase 13: Authentication & Settings UI (Week 19)

### 13.1 Authentication Forms
**Files**: `resources/js/pages/auth/*.tsx`

```tsx
// Brutalist login form
const BrutalistAuthForm = ({ title, children, submitText }) => (
  <div className="min-h-screen bg-neo-white dark:bg-neo-black flex items-center justify-center p-6">
    <div className="w-full max-w-md">
      <div className="neo-border neo-shadow bg-neo-yellow p-8">
        <h1 className="text-3xl font-black uppercase tracking-widest text-center text-neo-black mb-8">
          {title}
        </h1>
        
        <div className="space-y-6">
          {children}
        </div>
      </div>
    </div>
  </div>
)

// Brutalist form inputs
const BrutalistInput = ({ label, error, ...props }) => (
  <div className="space-y-2">
    <label className="font-black text-xs uppercase tracking-widest text-neo-black">
      {label}
    </label>
    <input
      className={`w-full neo-border neo-shadow-hover bg-neo-white px-4 py-3 font-mono font-bold placeholder:font-bold placeholder:text-neo-black/50 focus:shadow-none focus:translate-x-1 focus:translate-y-1 ${error ? 'border-red-500' : 'border-neo-black'}`}
      {...props}
    />
    {error && (
      <div className="neo-border bg-red-500 p-2">
        <p className="font-black text-xs text-white uppercase">{error}</p>
      </div>
    )}
  </div>
)
```

### 13.2 Settings & Profile Components
**Files**: `resources/js/pages/settings/*.tsx`

```tsx
// Settings layout with brutal navigation
const BrutalistSettingsLayout = ({ children }) => (
  <div className="flex min-h-screen bg-neo-white dark:bg-neo-black">
    <aside className="w-64 bg-neo-black neo-border-r">
      <div className="p-6">
        <h2 className="font-black text-xl uppercase tracking-widest text-neo-white mb-6">
          SETTINGS
        </h2>
        <nav className="space-y-2">
          <BrutalistNavItem href="/settings/profile" active>PROFILE</BrutalistNavItem>
          <BrutalistNavItem href="/settings/password">PASSWORD</BrutalistNavItem>
          <BrutalistNavItem href="/settings/appearance">APPEARANCE</BrutalistNavItem>
        </nav>
      </div>
    </aside>
    
    <main className="flex-1 p-8">
      {children}
    </main>
  </div>
)

const BrutalistNavItem = ({ href, children, active }) => (
  <Link
    href={href}
    className={`block px-4 py-3 font-black text-sm uppercase tracking-wide transition-all ${
      active 
        ? 'bg-neo-green text-neo-black' 
        : 'text-neo-white hover:bg-neo-white hover:text-neo-black'
    }`}
  >
    {children}
  </Link>
)
```

## Phase 14: Notification & Toast System (Week 20)

### 14.1 Brutal Notification Components
**File**: `resources/js/components/ui/neo-toast.tsx`

```tsx
// Neobrutalist toast notifications
export const BrutalistToast = ({ toast }) => {
  const colorMap = {
    success: 'bg-neo-green',
    error: 'bg-red-500',
    warning: 'bg-neo-yellow',
    info: 'bg-neo-blue',
    default: 'bg-neo-pink'
  }

  return (
    <div className={`neo-border neo-shadow ${colorMap[toast.type || 'default']} p-4 animate-slide-up max-w-md`}>
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-black uppercase tracking-wide text-neo-black text-sm mb-1">
            {toast.title || 'NOTIFICATION'}
          </h4>
          <p className="font-bold text-neo-black text-sm">
            {toast.message}
          </p>
        </div>
        <Button
          variant="ghost" 
          size="icon"
          className="text-neo-black hover:bg-neo-black hover:text-neo-white neo-border"
          onClick={() => toast.dismiss()}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
      
      {toast.action && (
        <div className="mt-3">
          <Button
            variant="outline"
            size="sm"
            className="font-black uppercase border-neo-black text-neo-black hover:bg-neo-black hover:text-neo-white"
            onClick={toast.action.onClick}
          >
            {toast.action.label}
          </Button>
        </div>
      )}
    </div>
  )
}
```

## Implementation Summary

This expanded implementation plan now covers **every major frontend component** in the Beat Forge application outside of the Filament admin panel:

### Core Application Areas Covered:
- **Dashboard & Navigation**: App header, sidebar, main dashboard layout
- **Audio Player System**: Main player, multi-track stems, waveform visualization
- **Upload Management**: Music library cards, upload forms, processing panels
- **Analysis Features**: Audio analysis displays, similar tracks discovery
- **Contest System**: Contest listings, brutalist data tables
- **Authentication**: Login, register, password reset forms
- **Settings & Profile**: User settings, appearance controls
- **Welcome/Landing**: Marketing pages with neobrutalist aesthetic
- **Notifications**: Toast system, progress indicators
- **Form Components**: All input types, validation displays
- **Utility Components**: Badges, buttons, cards, dialogs, dropdowns

### Key Design Principles Applied:
1. **Sharp geometric shapes** replacing all rounded corners
2. **Bold, high-contrast colors** from the specified palette
3. **Cabinet Grotesk typography** throughout all components  
4. **Harsh drop shadows** for depth and dimension
5. **Monospace fonts** for technical data and time displays
6. **Uppercase text treatment** for labels and headers
7. **Thick borders** (3px) on all interactive elements
8. **Hover animations** with shadow and position transforms

This comprehensive plan ensures that every user-facing component gets the full neobrutalist treatment while maintaining the application's core functionality and user experience.
