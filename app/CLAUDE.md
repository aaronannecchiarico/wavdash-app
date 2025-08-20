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
- **Complete fresh migration**: `php artisan migrate:fresh-with-microservice --seed` (includes microservice cleanup and storage clearing)
- **Seeders**: `php artisan db:seed`
- **Clear uploads**: `php artisan uploads:clear` (clears all upload files from storage)

### Audio Microservice Integration
- **Check microservice status**: `php artisan audio:migrate --type=fresh --force` (check if migration endpoints are available)
- **Clean microservice only**: `php artisan audio:migrate --type=fresh --force --silent` (clean Redis cache, task data, storage)
- **Complete system reset**: `php artisan migrate:fresh-with-microservice --seed` (Laravel + microservice + storage clearing)
- **Migration types**: `fresh` (complete reset), `migrate-only` (clear cache only), `seed-only` (reseed data only)

### Storage Management
- **Clear upload storage**: `php artisan uploads:clear --force` (removes all upload files without confirmation)
- **Complete storage clear**: Included in `migrate:fresh-with-microservice` (clears uploads, processed, stems, and stream files)
- Upload files are organized by user and date: `uploads/{user_id}/{Y/m/d}/filename`
- Stream files follow same structure: `uploads/stream/{user_id}/{Y/m/d}/filename.ogg`
- Storage directories cleared: `private/uploads`, `private/processed`, `private/stems`, `public/uploads/stream`

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

===

<laravel-boost-guidelines>
=== boost rules ===

## Laravel Boost
- Laravel Boost is an MCP server that comes with powerful tools designed specifically for this application. Use them.

## Artisan
- Use the `list-artisan-commands` tool when you need to call an Artisan command to double check the available parameters.

## URLs
- Whenever you share a project URL with the user you should use the `get-absolute-url` tool to ensure you're using the correct scheme, domain / IP, and port.

## Tinker / Debugging
- You should use the `tinker` tool when you need to execute PHP to debug code or query Eloquent models directly.
- Use the `database-query` tool when you only need to read from the database.

## Reading Browser Logs With the `browser-logs` Tool
- You can read browser logs, errors, and exceptions using the `browser-logs` tool from Boost.
- Only recent browser logs will be useful - ignore old logs.

## Searching Documentation (Critically Important)
- Boost comes with a powerful `search-docs` tool you should use before any other approaches. This tool automatically passes a list of installed packages and their versions to the remote Boost API, so it returns only version-specific documentation specific for the user's circumstance. You should pass an array of packages to filter on if you know you need docs for particular packages.
- The 'search-docs' tool is perfect for all Laravel related packages, including Laravel, Inertia, Livewire, Filament, Tailwind, Pest, Nova, Nightwatch, etc.
- You must use this tool to search for Laravel-ecosystem documentation before falling back to other approaches.
- Search the documentation before making code changes to ensure we are taking the correct approach.
- Use multiple, broad, simple, topic based queries to start. For example: `['rate limiting', 'routing rate limiting', 'routing']`.

### Available Search Syntax
- You can and should pass multiple queries at once. The most relevant results will be returned first.

1. Simple Word Searches with auto-stemming - query=authentication - finds 'authenticate' and 'auth'
2. Multiple Words (AND Logic) - query=rate limit - finds knowledge containing both "rate" AND "limit"
3. Quoted Phrases (Exact Position) - query="infinite scroll" - Words must be adjacent and in that order
4. Mixed Queries - query=middleware "rate limit" - "middleware" AND exact phrase "rate limit"
5. Multiple Queries - queries=["authentication", "middleware"] - ANY of these terms


=== inertia-laravel/core rules ===

## Inertia Core

- Inertia.js components should be placed in the `resources/js/Pages` directory unless specified differently in the JS bundler (vite.config.js).
- Use `Inertia::render()` for server-side routing instead of traditional Blade views.

<code-snippet lang="php" name="Inertia::render Example">
// routes/web.php example
Route::get('/users', function () {
    return Inertia::render('Users/Index', [
        'users' => User::all()
    ]);
});
</code-snippet>


=== inertia-laravel/v2 rules ===

## Inertia v2

- Make use of all Inertia features from v1 & v2. Check the documentation before making any changes to ensure we are taking the correct approach.

### Inertia v2 New Features
- Polling
- Prefetching
- Deferred props
- Infinite scrolling using merging props and `WhenVisible`
- Lazy loading data on scroll

### Deferred Props & Empty States
- When using deferred props on the frontend, you should add a nice empty state with pulsing / animated skeleton.


=== laravel/core rules ===

## Do Things the Laravel Way

- Use `php artisan make:` commands to create new files (i.e. migrations, controllers, models, etc.). You can list available Artisan commands using the `list-artisan-commands` tool.
- If you're creating a generic PHP class, use `artisan make:class`.
- Pass `--no-interaction` to all Artisan commands to ensure they work without user input. You should also pass the correct `--options` to ensure correct behavior.

### Database
- Always use proper Eloquent relationship methods with return type hints. Prefer relationship methods over raw queries or manual joins.
- Use Eloquent models and relationships before suggesting raw database queries
- Avoid `DB::`; prefer `Model::query()`. Generate code that leverages Laravel's ORM capabilities rather than bypassing them.
- Generate code that prevents N+1 query problems by using eager loading.
- Use Laravel's query builder for very complex database operations.

### Model Creation
- When creating new models, create useful factories and seeders for them too. Ask the user if they need any other things, using `list-artisan-commands` to check the available options to `php artisan make:model`.

### APIs & Eloquent Resources
- For APIs, default to using Eloquent API Resources and API versioning unless existing API routes do not, then you should follow existing application convention.

### Controllers & Validation
- Always create Form Request classes for validation rather than inline validation in controllers. Include both validation rules and custom error messages.
- Check sibling Form Requests to see if the application uses array or string based validation rules.

### Queues
- Use queued jobs for time-consuming operations with the `ShouldQueue` interface.

### Authentication & Authorization
- Use Laravel's built-in authentication and authorization features (gates, policies, Sanctum, etc.).

### URL Generation
- When generating links to other pages, prefer named routes and the `route()` function.

### Configuration
- Use environment variables only in configuration files - never use the `env()` function directly outside of config files. Always use `config('app.name')`, not `env('APP_NAME')`.

### Testing
- When creating models for tests, use the factories for the models. Check if the factory has custom states that can be used before manually setting up the model.
- Faker: Use methods such as `$this->faker->word()` or `fake()->randomDigit()`. Follow existing conventions whether to use `$this->faker` or `fake()`.
- When creating tests, make use of `php artisan make:test [options] <name>` to create a feature test, and pass `--unit` to create a unit test. Most tests should be feature tests.

### Vite Error
- If you receive an "Illuminate\Foundation\ViteException: Unable to locate file in Vite manifest" error, you can run `npm run build` or ask the user to run `npm run dev` or `composer run dev`.


=== laravel/v12 rules ===

## Laravel 12

- Use the `search-docs` tool to get version specific documentation.
- Since Laravel 11, Laravel has a new streamlined file structure which this project uses.

### Laravel 12 Structure
- No middleware files in `app/Http/Middleware/`.
- `bootstrap/app.php` is the file to register middleware, exceptions, and routing files.
- `bootstrap/providers.php` contains application specific service providers.
- **No app\Console\Kernel.php** - use `bootstrap/app.php` or `routes/console.php` for console configuration.
- **Commands auto-register** - files in `app/Console/Commands/` are automatically available and do not require manual registration.

### Database
- When modifying a column, the migration must include all of the attributes that were previously defined on the column. Otherwise, they will be dropped and lost.
- Laravel 11 allows limiting eagerly loaded records natively, without external packages: `$query->latest()->limit(10);`.

### Models
- Casts can and likely should be set in a `casts()` method on a model rather than the `$casts` property. Follow existing conventions from other models.


=== pint/core rules ===

## Laravel Pint Code Formatter

- You must run `vendor/bin/pint --dirty` before finalizing changes to ensure your code matches the project's expected style.
- Do not run `vendor/bin/pint --test`, simply run `vendor/bin/pint` to fix any formatting issues.


=== inertia-react/core rules ===

## Inertia + React

- Use `router.visit()` or `<Link>` for navigation instead of traditional links.

<code-snippet lang="react" name="Inertia Client Navigation">
    import { Link } from '@inertiajs/react'

    <Link href="/">Home</Link>
</code-snippet>

- For form handling, use `router.post` and related methods. Do not use regular forms.

<code-snippet lang="react" name="Inertia React Form Example">
import { useState } from 'react'
import { router } from '@inertiajs/react'

export default function Edit() {
    const [values, setValues] = useState({
        first_name: "",
        last_name: "",
        email: "",
    })

    function handleChange(e) {
        const key = e.target.id;
        const value = e.target.value

        setValues(values => ({
            ...values,
            [key]: value,
        }))
    }

    function handleSubmit(e) {
        e.preventDefault()

        router.post('/users', values)
    }

    return (
    <form onSubmit={handleSubmit}>
        <label htmlFor="first_name">First name:</label>
        <input id="first_name" value={values.first_name} onChange={handleChange} />
        <label htmlFor="last_name">Last name:</label>
        <input id="last_name" value={values.last_name} onChange={handleChange} />
        <label htmlFor="email">Email:</label>
        <input id="email" value={values.email} onChange={handleChange} />
        <button type="submit">Submit</button>
    </form>
    )
}
</code-snippet>


=== tailwindcss/core rules ===

## Tailwind Core

- Use Tailwind CSS classes to style HTML, check and use existing tailwind conventions within the project before writing your own.
- Offer to extract repeated patterns into components that match the project's conventions (i.e. Blade, JSX, Vue, etc..)
- Think through class placement, order, priority, and defaults - remove redundant classes, add classes to parent or child carefully to limit repetition, group elements logically
- You can use the `search-docs` tool to get exact examples from the official documentation when needed.

### Spacing
- When listing items, use gap utilities for spacing, don't use margins.

    <code-snippet name="Valid Flex Gap Spacing Example" lang="html">
        <div class="flex gap-8">
            <div>Superior</div>
            <div>Michigan</div>
            <div>Erie</div>
        </div>
    </code-snippet>


### Dark Mode
- If existing pages and components support dark mode, new pages and components must support dark mode in a similar way, typically using `dark:`.


=== tailwindcss/v4 rules ===

## Tailwind 4

- Always use Tailwind CSS v4 - do not use the deprecated utilities.
- `corePlugins` is not supported in Tailwind v4.
- In Tailwind v4, you import Tailwind using a regular CSS `@import` statement, not using the `@tailwind` directives used in v3:

<code-snippet name="Tailwind v4 Import Tailwind Diff" lang="diff"
   - @tailwind base;
   - @tailwind components;
   - @tailwind utilities;
   + @import "tailwindcss";
</code-snippet>


### Replaced Utilities
- Tailwind v4 removed deprecated utilities. Do not use the deprecated option - use the replacement.
- Opacity values are still numeric.

| Deprecated |	Replacement |
|------------+--------------|
| bg-opacity-* | bg-black/* |
| text-opacity-* | text-black/* |
| border-opacity-* | border-black/* |
| divide-opacity-* | divide-black/* |
| ring-opacity-* | ring-black/* |
| placeholder-opacity-* | placeholder-black/* |
| flex-shrink-* | shrink-* |
| flex-grow-* | grow-* |
| overflow-ellipsis | text-ellipsis |
| decoration-slice | box-decoration-slice |
| decoration-clone | box-decoration-clone |


=== tests rules ===

## Test Enforcement

- Every change must be programmatically tested. Write a new test or update an existing test, then run the affected tests to make sure they pass.
- Run the minimum number of tests needed to ensure code quality and speed. Use `php artisan test` with a specific filename or filter.
</laravel-boost-guidelines>