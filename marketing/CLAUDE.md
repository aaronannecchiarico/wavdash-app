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

## Architecture

### Routing
- File-based routing via `src/pages/` directory
- Each `.astro` or `.md` file in `src/pages/` becomes a route based on filename
- Example: `src/pages/index.astro` → `/`

### Component Structure
- **Astro Pages**: Located in `src/pages/` for routing
- **React Components**: Can be placed in `src/components/` (not created yet but standard convention)
- **Hybrid Approach**: Astro components can import and use React components via the `@astrojs/react` integration

### Styling System
- **Tailwind CSS v4** is configured as a Vite plugin (not PostCSS)
- Global styles imported via `src/styles/global.css`
- Must import `@import "tailwindcss";` in CSS files to enable Tailwind

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
- Astro pages currently handle their own `<html>`, `<head>`, and `<body>` tags
- Global CSS is imported in the frontmatter of `.astro` files
- No shared layout component exists yet (pages define full HTML structure)

### Current State
- Project is in early stages with minimal boilerplate
- Only index page exists (`src/pages/index.astro`)
- No components directory created yet
- Single global CSS file for Tailwind imports
