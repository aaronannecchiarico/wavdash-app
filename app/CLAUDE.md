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

## Testing with Inertia.js

This application uses comprehensive Inertia.js testing patterns to ensure proper server-side rendering and data flow between Laravel controllers and React components.

### Testing Setup

**Required Import:**
```php
use Inertia\Testing\AssertableInertia as Assert;
```

**Basic Test Structure:**
```php
public function test_controller_returns_proper_inertia_response()
{
    $user = User::factory()->create();
    
    $response = $this->actingAs($user)->get(route('route.name'));
    
    $response->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('page/component')
            ->has('data.field')
            ->where('data.id', $expectedValue)
        );
}
```

### Common Testing Patterns

**1. Component Assertion:**
```php
->assertInertia(fn (Assert $page) => $page
    ->component('uploads/index') // Verify correct component
)
```

**2. Data Structure Testing:**
```php
->assertInertia(fn (Assert $page) => $page
    ->has('uploads.data', 3) // Assert collection size
    ->has('uploads.data.0', fn (Assert $upload) => $upload
        ->has('id')
        ->has('title')
        ->has('status')
        ->etc() // Allow additional fields
    )
)
```

**3. Specific Value Assertions:**
```php
->assertInertia(fn (Assert $page) => $page
    ->where('upload.data.id', $upload->id)
    ->where('filters.status', 'ready')
)
```

**4. Resource Structure Testing:**
```php
->assertInertia(fn (Assert $page) => $page
    ->has('upload.data', fn (Assert $upload) => $upload
        ->has('id')
        ->has('title')
        ->has('user', fn (Assert $user) => $user
            ->has('id')
            ->has('name')
        )
        ->etc()
    )
)
```

### Controller-Specific Examples

**Upload Controller:**
```php
// Index page with pagination and filtering
$response->assertOk()
    ->assertInertia(fn (Assert $page) => $page
        ->component('uploads/index')
        ->has('uploads.data')
        ->has('uploads.links')
        ->has('uploads.meta')
        ->has('filters')
        ->has('filterOptions')
    );

// Show page with resource data
$response->assertOk()
    ->assertInertia(fn (Assert $page) => $page
        ->component('uploads/show')
        ->has('upload.data', fn (Assert $upload) => $upload
            ->where('id', $upload->id)
            ->has('title')
            ->has('filename')
            ->has('user')
            ->etc()
        )
    );
```

**Analysis Controller:**
```php
// Analysis page with service status
$response->assertOk()
    ->assertInertia(fn (Assert $page) => $page
        ->component('uploads/analysis')
        ->has('upload.data')
        ->has('analysis_service', fn (Assert $service) => $service
            ->has('enabled')
            ->has('available')
        )
    );
```

### Testing Considerations

**Resource Wrapping:**
- Laravel resources wrap data in `.data` property
- Always use `upload.data` not `upload` for resource assertions
- Pagination data includes `.links` and `.meta` properties

**Factory Hooks:**
- Be aware of model factory `afterCreating` hooks
- Use `make()` then `save()` to bypass hooks when needed
- Use `state(['field' => 'value'])` to override defaults

**Authentication:**
- Always use `$this->actingAs($user)` for protected routes
- Test authorization with different users when applicable

**Data Types:**
- Be precise with numeric types (int vs float)
- Use exact values for assertions (`->where('id', 1)`)

### Best Practices

1. **Test Component and Data Together**: Always verify both the correct component loads and contains expected data
2. **Use Nested Assertions**: Structure assertions to match your resource/component hierarchy  
3. **Test Edge Cases**: Include authorization, validation, and error scenarios
4. **Mock External Services**: Use fakes for storage, queues, and external APIs
5. **Verify Relationships**: Test that related data (user, analysis) is properly loaded

### Example Test File Structure

```php
class UploadControllerTest extends TestCase
{
    use RefreshDatabase;

    #[Test]
    public function index_requires_authentication() { /* ... */ }
    
    #[Test] 
    public function index_returns_proper_inertia_response() { /* ... */ }
    
    #[Test]
    public function show_returns_proper_inertia_response() { /* ... */ }
    
    #[Test]
    public function show_requires_upload_authorization() { /* ... */ }
}
```

This testing approach ensures that your Inertia.js application works correctly across the full stack, from Laravel controllers to React components.