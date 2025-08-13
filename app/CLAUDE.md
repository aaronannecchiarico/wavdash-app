# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (React/TypeScript)
- **Build**: `npm run build` or `npm run build:ssr` (for SSR)
- **Development**: `npm run dev` (run frontend development server)
- **Full development stack**: `composer run dev` (starts Laravel server, queue worker, logs, and Vite)
- **Linting**: `npm run lint` (ESLint with auto-fix)
- **Type checking**: `npm run types` (TypeScript type checking)
- **Formatting**: `npm run format` or `npm run format:check` (Prettier)

### Backend (Laravel/PHP)
- **Testing**: `composer run test` (clears config and runs PHPUnit)
- **Development with SSR**: `composer run dev:ssr`
- **Individual commands**: `php artisan serve`, `php artisan queue:listen`, `php artisan pail`

### Database
- **Migrations**: `php artisan migrate`
- **Fresh migration**: `php artisan migrate:fresh --seed` (drops all tables, re-runs migrations, and seeds data)
- **Seeders**: `php artisan db:seed`
- **Clear uploads**: `php artisan uploads:clear` (clears all upload files from storage)

### Storage Management
- **Clear upload storage**: `php artisan uploads:clear --force` (removes all upload files without confirmation)
- Upload files are organized by user and date: `uploads/{user_id}/{Y/m/d}/filename`
- Stream files follow same structure: `uploads/stream/{user_id}/{Y/m/d}/filename.ogg`

## Architecture Overview

This is a Laravel 12 + React + Inertia.js application for audio file management and processing, functioning as a "Beat Forge" platform.

### Core Components

**Laravel Backend**:
- **Audio Processing**: Uses Laravel FFMpeg to convert uploads to OGG format for streaming
- **Queue Jobs**: `ProcessAudioUpload` handles async audio conversion
- **Models**: `Upload`, `Contest`, `User`, `Vote` with relationships
- **Broadcasting**: Laravel Reverb for real-time upload processing updates
- **Authentication**: Laravel Breeze with Inertia

**React Frontend**:
- **Inertia.js**: For SPA-like experience with server-side routing
- **UI Components**: Shadcn/ui with Radix UI primitives
- **Audio Playback**: WaveSurfer.js integration for waveform visualization
- **Styling**: Tailwind CSS with dark mode support
- **Icons**: Lucide React

### Audio Processing Flow

1. User uploads audio file → stored in `storage/app/private/uploads/{user_id}/{Y/m/d}/filename`
2. `ProcessAudioUpload` job dispatched → converts to OGG format
3. Streaming version saved to `storage/app/public/uploads/stream/{user_id}/{Y/m/d}/filename.ogg`
4. `UploadProcessed` event broadcasted for real-time UI updates
5. Upload status updated from `pending` → `processing` → `ready`/`failed`

### Key Models & Relationships

- **Upload**: Core audio file model with user relationship
- **Contest**: Music competitions with user entries
- **ContestUser**: Pivot table linking contests and users via uploads
- **Vote**: User voting system for contest entries

### Directory Structure

**Laravel Specific**:
- Controllers: `/app/Http/Controllers/*`
- Models: `/app/Models/*` 
- Jobs: `/app/Jobs/*`
- Events: `/app/Events/*`
- Policies: `/app/Policies/*`
- Routes: `/routes/*` (web.php, auth.php, settings.php)
- Database: `/database/migrations/*`, `/database/factories/*`

**React/Frontend**:
- Components: `/resources/js/components/*`
- Pages: `/resources/js/pages/*` (Inertia pages)
- Layouts: `/resources/js/layouts/*`
- Hooks: `/resources/js/hooks/*`
- Types: `/resources/js/types/*`
- Utils: `/resources/js/lib/*`

## Important Notes

### Laravel 11+ Conventions
- Service providers registered in `bootstrap/providers.php` (not `config/app.php`)
- Middleware registered in `bootstrap/app.php` (not `app/Http/Kernel.php`)
- Console commands in `routes/console.php` (not `app/Console/Kernel.php`)

### Inertia.js Patterns
- All routing handled by Laravel (no React Router)
- Use `<Link>` from `@inertiajs/react` for internal navigation
- Form state managed with `useForm()` from `@inertiajs/react`
- Data passed from controllers via `Inertia::render()`
- Avoid `useEffect` for data fetching - prefer server-side data loading

### Audio Processing Integration
- **Basic Processing**: Laravel FFMpeg for audio format conversion (MP3/WAV → OGG)
- **Advanced Analysis**: Optional FastAPI microservice integration (see `API_INTEGRATION_GUIDE.md`)
- **Analysis Models**: `UploadAnalysisTask` (tracks job status) and `UploadAnalysis` (stores results)
- **Configuration**: Enable via `AUDIO_ANALYSIS_ENABLED=true` and `AUDIO_ANALYSIS_BASE_URL`
- **Analysis Data**: Musical key, BPM, loudness, brightness, timbral complexity, etc.
- **Similar Track Finding**: Built-in algorithm for music recommendation based on analysis
- **Frontend-Triggered**: Analysis initiated by user action via `UploadAnalysisController`, not automatic

### Analysis Endpoints & Pages
- `POST /uploads/{upload}/analysis` - Start analysis (redirects back with flash message)
- `GET /uploads/{upload}/analysis` - Analysis page (Inertia: `uploads/analysis`)
- `DELETE /uploads/{upload}/analysis` - Delete analysis (redirects back with flash message)
- `GET /uploads/{upload}/analysis/similar` - Similar tracks page (Inertia: `uploads/similar`)
- `GET /api/analysis/status` - Service status API endpoint (JSON response)

### File Naming Conventions
- React components/hooks: `kebab-case.tsx` (e.g., `music-library-card.tsx`)
- Use `.tsx` for components and hooks (not `.ts`)

### Broadcasting & Real-time Updates
- Laravel Reverb configured for WebSocket connections
- Upload processing status broadcasted via `UploadProcessed` event
- Frontend listens for real-time updates during audio processing