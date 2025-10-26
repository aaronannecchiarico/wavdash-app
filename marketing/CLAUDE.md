# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Astro-based marketing website with React integration and Tailwind CSS v4. The project uses a minimal starter template configuration and is designed for building static marketing pages.

## Technology Stack

- **Framework**: Astro 5.14.6 with React 19.2.0 integration
- **Styling**: Tailwind CSS v4.1.14 (configured via Vite plugin)
- **TypeScript**: Strict mode enabled with Astro's strict tsconfig
- **Build Tool**: Astro's built-in Vite-based tooling

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:4321)
npm run dev

# Build for production (outputs to ./dist/)
npm run build

# Preview production build locally
npm run preview

# Run Astro CLI commands
npm run astro -- <command>
```

## Installing Packages

Use `astro add` for integrations: Use astro add for official integrations (e.g. astro add tailwind, astro add react).
For other packages, install using npm rather than editing package.json directly.

## Git Commit Guidelines

- Do NOT include "Co-Authored-By: Claude" in commit messages
- Do NOT include promotional links like "Generated with Claude Code" in commit messages
- Keep commit messages clear, concise, and professional

## Architecture

### Domain Structure
- **Marketing Site**: `wavdash.com` (this Astro application)
- **Application**: `app.wavdash.com` (Laravel application)
- **Development**: `localhost:4321` (Astro) and `localhost:8000` (Laravel)

### Authentication Architecture
- Cross-domain authentication between marketing site and Laravel app
- Session-based authentication using shared cookies (domain: `.wavdash.com` in production)
- Environment-specific configuration via `PUBLIC_APP_URL` environment variable
- See `docs/authentication-integration.md` for complete implementation details

**Authentication Flow:**
1. Astro pages check auth status via Laravel API (`/api/auth/check`) during SSR
2. Laravel returns authentication state and user data
3. Header component receives `isLoggedIn` prop and renders appropriate buttons
4. Login/Register/Dashboard buttons link to Laravel app URLs

**Environment Variables:**
- `PUBLIC_APP_URL`: Laravel application URL (e.g., `https://app.wavdash.com` or `http://localhost:8000`)

### File Upload Architecture
- Drag-and-drop file upload from marketing site to Laravel application
- Files uploaded directly to Laravel API endpoint (`/api/upload-temp`)
- Temporary storage with UUID-based filenames for security
- Seamless redirect to Laravel onboarding flow after upload
- See `docs/file-upload-integration.md` for complete implementation details

**Upload Flow:**
1. User drags audio file onto marketing site upload zone (React component)
2. File uploads to Laravel with progress tracking (XMLHttpRequest)
3. Laravel validates, stores temporarily, and returns upload ID
4. Marketing site redirects to Laravel onboarding: `app.wavdash.com/onboard?upload={uuid}`
5. Laravel retrieves file metadata and prompts login if needed
6. After auth, file moves to permanent storage and processing begins

**Components:**
- `FileUploadZone.tsx`: React component for drag-and-drop with progress tracking
- Supports: MP3, WAV, FLAC, AAC, OGG, M4A (max 100MB)
- Includes client-side and server-side validation

### Routing
- File-based routing via `src/pages/` directory
- Each `.astro` or `.md` file in `src/pages/` becomes a route based on filename
- Example: `src/pages/index.astro` → `/`
- API endpoints in `src/pages/api/` for server-side logic

### Component Structure
- **Astro Pages**: Located in `src/pages/` for routing
- **Astro Layouts**: Located in `src/layouts/` for shared page structure
- **Astro Components**: Located in `src/components/` for static, non-interactive components
- **React Components**: Located in `src/components/react/` for interactive components requiring client-side JavaScript
- **Utilities**: Located in `src/lib/` for helper functions and shared logic
- **Hybrid Approach**: Astro components can import and use React components via the `@astrojs/react` integration

#### Component Inventory

**Layouts**:
- `MainLayout.astro` - Shared page layout with authentication checking, meta tags, and Header component

**Utilities**:
- `auth.ts` - Authentication helper for checking user auth status with Laravel backend

**Astro Components** (Static, Zero JavaScript):
- `FeatureCard.astro` - Feature display cards with icon, title, description, and features list
- `ProcessStep.astro` - Process step cards with step number and optional arrow indicator
- `StatsDisplay.astro` - Statistics display with large numbers and labels
- `TechBadge.astro` - Technology badge components for technical features section

**React Components** (Interactive, Client-Side Hydration):
- `Header.tsx` - Responsive navigation header with auth state (uses `client:load`)
  - Desktop: 3-column grid layout with centered nav links and right-aligned auth links
  - Mobile: Hamburger menu with shadcn/ui Sheet component for slide-out navigation
  - Includes all nav links (Features, How It Works, Pricing) and auth links in mobile menu
  - Auth links use `PUBLIC_APP_URL` to link to Laravel app (login, register, dashboard)
  - Displays Login/Register when logged out, Dashboard when logged in
- `Icon.tsx` - Wrapper component for Lucide React icons (allows use in Astro components)
- `BarVisualizer.tsx` - Frequency band audio visualizer with agent states (connecting, listening, speaking, thinking) and demo mode
- `StaticWaveform.tsx` - Lightweight static waveform visualization using canvas with seeded pseudo-random heights
- `Orb.tsx` - 3D animated orb using Three.js/React Three Fiber with shader-based visuals (requires WebGL)
- `OrbWithFallback.tsx` - Orb wrapper with mobile fallback (shows static gradient on mobile devices)
- `AudioAnalysisDemo.tsx` - Complete audio analysis demo showcasing BPM, key detection, loudness, and stem separation (uses `client:visible`)

### Styling System
- **Tailwind CSS v4** is configured as a Vite plugin (not PostCSS)
- Global styles imported via `src/styles/global.css`
- Must import `@import "tailwindcss";` in CSS files to enable Tailwind
- **Neobrutalist Design System** implemented with:
  - CSS custom properties for brand colors (`--neo-green`, `--neo-pink`, `--neo-yellow`, `--neo-blue`)
  - Hard shadows (no blur): `--neo-shadow`, `--neo-shadow-sm`, `--neo-shadow-lg`
  - Utility classes: `.neo-border`, `.neo-shadow`, `.neo-transition`, `.neo-hover-lift`
  - Zero border radius (sharp rectangles on all components)
  - 3px solid black borders
  - High contrast color palette

### Static Assets
- Place static files (images, fonts, etc.) in `public/` directory
- Accessed directly from root path (e.g., `/favicon.svg`)

## Key Configuration Details

### Tailwind CSS v4 Setup
- Configured via `@tailwindcss/vite` plugin in `astro.config.mjs`
- Import with `@import "tailwindcss";` in CSS files (not the typical `@tailwind` directives)
- This is Tailwind CSS v4, which uses a different configuration approach than v3

### TypeScript Configuration
- Uses Astro's strict TypeScript configuration
- JSX is configured for React (`"jsx": "react-jsx"`)
- JSX import source set to `"react"`

### React Integration
- React components must be explicitly marked for client-side hydration using Astro's client directives:
  - `client:load` - Hydrate immediately on page load
  - `client:idle` - Hydrate when the browser is idle
  - `client:visible` - Hydrate when component enters viewport
  - `client:media` - Hydrate based on media query
- By default, React components are rendered to static HTML without JavaScript

## Project-Specific Patterns

### Page Layout
- **Layout Component**: `src/layouts/MainLayout.astro` provides shared structure for all pages
- The layout handles authentication checking via `checkAuthStatus()` helper
- Pages use the layout by importing and wrapping content with `<MainLayout>` component
- Layout accepts props: `title`, `description`, `ogTitle`, `ogDescription`
- Global CSS, fonts, and meta tags are managed by the layout
- Header component receives authentication state from layout automatically

### Current State
- **Complete marketing landing page** for WavDash (AI-powered audio processing platform)
- Full neobrutalist design implementation migrated from Figma design
- **ElevenLabs UI Integration**: Professional audio visualization components adapted from ElevenLabs UI library
- Main page (`src/pages/index.astro`) includes all sections:
  - Hero section with grid pattern background
  - Features section (3 feature cards)
  - How It Works section (3-step process)
  - Technical Features section (6 tech badges)
  - **Demo section with Audio Analysis showcase** featuring:
    - 3D Orb background animation (Three.js/React Three Fiber) with mobile fallback
    - Interactive audio waveform visualization
    - Real-time analysis results display (BPM, Key, Time Signature, Loudness)
    - Stem separation preview with BarVisualizer
    - Static demo data (no file upload yet)
  - Social Proof section with statistics
  - Pricing section (free tier)
  - Community/Contest section
  - Footer CTA and footer navigation
- Component library complete with 11 reusable components
- Inter font loaded from Google Fonts (can be upgraded to Cabinet Grotesk)
- SEO meta tags and Open Graph tags implemented

### Dependencies
- **Three.js Stack**: `three`, `@react-three/fiber`, `@react-three/drei` for 3D Orb visualization
- **Utilities**: `clsx`, `tailwind-merge` for className utilities (via `cn()` helper in `src/lib/utils.ts`)
- **UI Components**: shadcn/ui components installed in `src/components/ui/`
  - `Sheet` component for mobile navigation menu (slide-out drawer)

### Known Issues
- None currently (previous AnimatedWaveform hydration warning resolved)
