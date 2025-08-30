# CLAUDE.md

This file provides structured guidance to Claude Code (claude.ai/code) when working with code in this repository. Follow the decision-making frameworks and reasoning patterns outlined below.

## Decision-Making Framework

When working with this codebase, use this systematic approach:

<decision_framework>
1. **Identify the task type**: Development, testing, debugging, or deployment
2. **Choose appropriate tools**: Use Laravel Boost tools first, then fallback to standard tools
3. **Follow project patterns**: Match existing code style and architecture
4. **Validate changes**: Run tests and linting before completion
5. **Document decisions**: Explain reasoning for complex choices
</decision_framework>

## Development Commands Decision Tree

### When to Use Each Command

<command_decision_tree>
**For Starting Development:**
- Fresh start with clean data: `php artisan migrate:fresh-with-microservice --seed`
- Continue existing work: `composer run dev`
- Frontend only changes: `npm run dev`

**For Testing Changes:**
- Run all tests: `composer run test`
- Specific test file: `php artisan test tests/Feature/SpecificTest.php`
- Type checking: `npm run types`

**For Deployment Preparation:**
- Build frontend: `npm run build` or `npm run build:ssr`
- Code formatting: `vendor/bin/pint --dirty`
- Final validation: `npm run lint && npm run types`
</command_decision_tree>

### Frontend (React/TypeScript)

<frontend_commands>
- **Build**: `npm run build` or `npm run build:ssr` (for SSR)
  - Use SSR build when working with server-side rendering features
- **Development**: `npm run dev` (run frontend development server)
  - Use for frontend-only changes that don't require Laravel backend
- **Full development stack**: `composer run dev` (starts Laravel server, queue worker, logs, and Vite)
  - Use when working on features that require both frontend and backend
- **Linting**: `npm run lint` (ESLint with auto-fix)
  - Run before committing changes
- **Type checking**: `npm run types` (TypeScript type checking)
  - Run after making TypeScript changes
- **Formatting**: `npm run format` or `npm run format:check` (Prettier)
  - Use for consistent code formatting
</frontend_commands>

### Backend (Laravel/PHP)

<backend_commands>
- **Development Server**: `composer run dev`
  - Starts all required services: Laravel server, queue worker, logs, and Vite
- **Testing**: `composer run test` (clears config and runs PHPUnit)
  - Always run before committing changes
- **Development with SSR**: `composer run dev:ssr`
  - Use when testing server-side rendering features
- **Individual commands**: `php artisan serve`, `php artisan queue:listen`, `php artisan pail`
  - Use for debugging specific services
</backend_commands>

### Database Operations Decision Framework

<database_decisions>
**Choose based on your goal:**

**Clean slate development:**
- Command: `php artisan migrate:fresh-with-microservice --seed`
- When: Starting new features, after major schema changes
- Effect: Complete system reset including microservice and storage

**Regular development:**
- Command: `php artisan migrate`
- When: Adding new migrations during development
- Effect: Applies new migrations only

**Data issues:**
- Command: `php artisan migrate:fresh --seed`
- When: Database inconsistencies, testing data problems
- Effect: Laravel reset only, preserves microservice state

**Storage cleanup:**
- Command: `php artisan uploads:clear --force`
- When: Storage space issues, testing upload features
- Effect: Removes all upload files
</database_decisions>

### Storage Management

<storage_management>
- **Clear upload storage**: `php artisan uploads:clear --force` (removes all upload files without confirmation)
- **Complete storage clear**: Included in `migrate:fresh-with-microservice` (clears uploads, processed, stems, and stream files)
- Upload files are organized by user and date: `uploads/{user_id}/{Y/m/d}/filename`
- Stream files follow same structure: `uploads/stream/{user_id}/{Y/m/d}/filename.ogg`
- Stem streaming files follow this structure: `uploads/stream/{user_id}/{Y/m/d}/stems/{upload_id}/[bass.ogg, drums.ogg, vocals.ogg, other.ogg]`
- Tempo streaming files follow this structure: `uploads/stream/{user_id}/{Y/m/d}/tempo/{upload_id}/[tempo-type-speed.ogg]`
- Storage directories cleared: `private/uploads`, `private/processed`, `private/stems`, `public/uploads/stream`
</storage_management>

### Audio Microservice Integration

<microservice_commands>
- **Check microservice status**: `php artisan audio:migrate --type=fresh --force`
  - Use to verify microservice connectivity
- **Clean microservice only**: `php artisan audio:migrate --type=fresh --force --silent`
  - Use when Laravel DB is fine but microservice needs reset
- **Complete system reset**: `php artisan migrate:fresh-with-microservice --seed`
  - Use for complete development environment reset
- **Migration types**: 
  - `fresh`: Complete reset of microservice data
  - `migrate-only`: Clear cache only
  - `seed-only`: Reseed data only
</microservice_commands>

### Cloudflare R2 Management

<r2_commands>
- **List buckets**: `npx wrangler r2 bucket list`
- **Create bucket**: `npx wrangler r2 bucket create <bucket-name>`
- **Delete bucket**: `npx wrangler r2 bucket delete <bucket-name>`
- **List objects in bucket**: `npx wrangler r2 object list <bucket-name>`
- **Enable public access**: `npx wrangler r2 bucket public <bucket-name> enable`
- **Disable public access**: `npx wrangler r2 bucket public <bucket-name> disable`
</r2_commands>

## Architecture Overview

This is a Laravel 12 + React + Inertia.js application for audio file management and processing, functioning as a "Beat Forge" platform with a **Filament v4 admin panel** for backend administration.

### Architecture Decision Framework

<architecture_thinking>
When making architectural decisions, consider:

1. **Data Flow**: Laravel → Inertia → React → User
2. **Processing Flow**: Upload → Queue → Analysis → Stream
3. **Authentication**: Separate admin and user systems
4. **Real-time Updates**: Laravel Reverb for WebSocket connections
5. **File Management**: Organized by user and date hierarchy
</architecture_thinking>

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

**Filament v4 Admin Panel**:
- **Version**: Filament v4.0.3 - Modern admin panel framework
- **Purpose**: Backend administration interface for managing users, uploads, contests, analysis tasks
- **Structure**: Organized with Resources, Pages, Tables, Forms, Infolists, and RelationManagers
- **Authentication**: Separate admin authentication from main user system
- **Real-time**: Integration with Laravel Reverb for live updates

### Audio Processing Flow

<processing_flow>
**Step-by-step reasoning:**

1. **Upload Receipt**: User uploads audio file → stored in `storage/app/private/uploads/{user_id}/{Y/m/d}/filename`
   - Why: Organized by user and date for easy management and cleanup

2. **Queue Dispatch**: `ProcessAudioUpload` job dispatched → converts to OGG format
   - Why: Async processing prevents UI blocking during conversion

3. **Stream Creation**: Streaming version saved to `storage/app/public/uploads/stream/{user_id}/{Y/m/d}/filename.ogg`
   - Why: Public directory allows direct web access for streaming

4. **Real-time Updates**: `UploadProcessed` event broadcasted for real-time UI updates
   - Why: Users see processing progress without page refresh

5. **Status Updates**: Upload status updated from `pending` → `processing` → `ready`/`failed`
   - Why: Clear status tracking allows proper UI state management
</processing_flow>

### Key Models & Relationships

<model_relationships>
- **Upload**: Core audio file model with user relationship
  - Belongs to User, has many Votes, belongs to many Contests
- **Contest**: Music competitions with user entries
  - Has many Users through ContestUser pivot, has many Uploads through relationships
- **ContestUser**: Pivot table linking contests and users via uploads
  - Facilitates many-to-many relationship with additional upload_id context
- **Vote**: User voting system for contest entries
  - Belongs to User and Upload, enables contest voting functionality
</model_relationships>

### Directory Structure

**Laravel Specific**:
- Controllers: `/app/Http/Controllers/*`
- Models: `/app/Models/*` 
- Jobs: `/app/Jobs/*`
- Events: `/app/Events/*`
- Policies: `/app/Policies/*`
- Routes: `/routes/*` (web.php, auth.php, settings.php)
- Database: `/database/migrations/*`, `/database/factories/*`

**Filament v4 Admin Panel**:
- Resources: `/app/Filament/Resources/*` (main resource classes)
- Pages: `/app/Filament/Resources/*/Pages/*` (List, Create, Edit, View pages)  
- Tables: `/app/Filament/Resources/*/Tables/*` (table definitions)
- Schemas: `/app/Filament/Resources/*/Schemas/*` (forms and infolists)
- RelationManagers: `/app/Filament/Resources/*/RelationManagers/*` (relationship tables)
- Custom Components: `/app/Filament/Infolists/Components/*` (custom infolist entries)

**React/Frontend**:
- Components: `/resources/js/components/*`
- Pages: `/resources/js/pages/*` (Inertia pages)
- Layouts: `/resources/js/layouts/*`
- Hooks: `/resources/js/hooks/*`
- Types: `/resources/js/types/*`
- Utils: `/resources/js/lib/*`

## Development Decision Framework

### Laravel 11+ Conventions Decision Tree

<laravel_conventions>
**When registering services, use this decision process:**

1. **Service Providers**: Register in `bootstrap/providers.php` (not `config/app.php`)
   - Why: Laravel 11+ uses streamlined file structure
2. **Middleware**: Register in `bootstrap/app.php` (not `app/Http/Kernel.php`)
   - Why: Centralized application configuration
3. **Console Commands**: Place in `routes/console.php` (not `app/Console/Kernel.php`)
   - Why: Auto-registration from `app/Console/Commands/` directory
</laravel_conventions>

### Inertia.js Development Patterns

<inertia_patterns>
**Decision framework for Inertia development:**

**Routing**: All routing handled by Laravel (no React Router)
- Why: Maintains server-side control and SEO benefits

**Navigation**: Use `<Link>` from `@inertiajs/react` for internal navigation
- Why: Preserves SPA-like experience with server-side routing

**Forms**: Use `useForm()` from `@inertiajs/react` for form state management
- Why: Integrates with Laravel validation and error handling

**Data Loading**: Pass data from controllers via `Inertia::render()`, avoid `useEffect` for data fetching
- Why: Server-side data loading is more reliable and SEO-friendly

<example_inertia_navigation>
```typescript
import { Link } from '@inertiajs/react'

// Correct approach
<Link href="/uploads">View Uploads</Link>

// Avoid regular anchor tags for internal navigation
// <a href="/uploads">View Uploads</a>
```
</example_inertia_navigation>
</inertia_patterns>

### Audio Processing Integration

<audio_processing_decisions>
**Choose processing approach based on requirements:**

**Basic Processing**: Laravel FFMpeg for audio format conversion (MP3/WAV → OGG)
- When: Simple format conversion needs
- Why: Built into Laravel, no external dependencies

**Advanced Analysis**: Optional FastAPI microservice integration
- When: Need musical analysis (BPM, key, etc.)
- Requirements: `AUDIO_ANALYSIS_ENABLED=true` and `AUDIO_ANALYSIS_BASE_URL`
- Models: `UploadAnalysisTask` (tracks job status) and `UploadAnalysis` (stores results)

**Analysis Data Types**: Musical key, BPM, loudness, brightness, timbral complexity
**Similar Track Finding**: Built-in algorithm for music recommendation based on analysis
**Trigger Method**: Frontend-triggered via `UploadAnalysisController`, not automatic
</audio_processing_decisions>

### Analysis Endpoints & Pages

<analysis_endpoints>
- `POST /uploads/{upload}/analysis` - Start analysis (redirects back with flash message)
- `GET /uploads/{upload}/analysis` - Analysis page (Inertia: `uploads/analysis`)
- `DELETE /uploads/{upload}/analysis` - Delete analysis (redirects back with flash message)
- `GET /uploads/{upload}/analysis/similar` - Similar tracks page (Inertia: `uploads/similar`)
- `GET /api/analysis/status` - Service status API endpoint (JSON response)
</analysis_endpoints>

### File Naming Conventions

<naming_conventions>
- React components/hooks: `kebab-case.tsx` (e.g., `music-library-card.tsx`)
- Use `.tsx` for components and hooks (not `.ts`)
- Why: Consistent with project conventions and TypeScript requirements
</naming_conventions>

### Broadcasting & Real-time Updates

<broadcasting_setup>
- Laravel Reverb configured for WebSocket connections
- Upload processing status broadcasted via `UploadProcessed` event
- Frontend listens for real-time updates during audio processing
- Why: Provides immediate feedback during long-running audio processing tasks
</broadcasting_setup>

## Filament v4 Admin Panel Structure & Usage

### Admin Panel Decision Framework

<admin_panel_decisions>
**Purpose**: Complete admin backend for managing users, uploads, contests, and analysis tasks
**Authentication**: Separate from main user system, accessed via `/admin` route
**File Organization**: Uses modern v4 structure with dedicated directories for each component type

**When to use Filament features:**
- **Resources**: For CRUD operations on models
- **RelationManagers**: For managing related data within resources
- **Custom Components**: Only when built-in components don't meet needs
- **Actions**: For custom operations on records
</admin_panel_decisions>

### Available Admin Resources

<admin_resources>
- **Users**: User management with profile information
- **Uploads**: Audio file management with processing status, analysis data
- **Contests**: Contest creation and management
- **Upload Analysis Tasks**: Audio analysis job tracking
- **Upload Analysis**: Stored analysis results (BPM, key, etc.)  
- **Upload Stem Tasks**: Audio stem separation job tracking
- **Upload Tempo Tasks**: Tempo analysis job tracking
</admin_resources>

### Filament v4 Component Structure

<filament_structure>
Each resource follows the standard Filament v4 pattern:
- **Resource Class**: Main resource definition (`*Resource.php`)
- **Pages**: List, Create, Edit, View pages in `/Pages/` subdirectory
- **Tables**: Table definitions in `/Tables/` subdirectory  
- **Schemas**: Form and Infolist schemas in `/Schemas/` subdirectory
- **RelationManagers**: For managing related data in `/RelationManagers/`
</filament_structure>

### Custom Components

<custom_components>
- **AudioPlayerEntry**: Custom infolist component for audio playback
- **ProcessingStatusEntry**: Custom component for upload processing status  
- **FileSizeEntry**: Custom component for file size display
- **Usage Rule**: Use these existing components for consistency before creating new ones
</custom_components>

### Filament v4 Best Practices for this Project

<filament_best_practices>
- Always use `make:filament-resource` to create new resources
- Avoid using custom components when possible and opt for built-in Filament components
- Use Filament's HeroIcon class for icons
- Follow existing directory structure and naming conventions
</filament_best_practices>

## Testing Framework with Inertia.js

This application uses comprehensive Inertia.js testing patterns to ensure proper server-side rendering and data flow between Laravel controllers and React components.

### Testing Decision Framework

<testing_decisions>
**Choose testing approach based on:**

1. **Authentication Testing**: Use `$this->actingAs($user)` for protected routes
2. **Component Testing**: Verify both component name and data structure
3. **Resource Testing**: Always test `.data` property for Laravel resources
4. **Relationship Testing**: Verify related data is properly loaded and structured
</testing_decisions>

### Testing Setup

<testing_setup>
**Required Import:**
```php
use Inertia\Testing\AssertableInertia as Assert;
```

**Basic Test Structure with Reasoning:**
```php
public function test_controller_returns_proper_inertia_response()
{
    // Arrange: Create test data
    $user = User::factory()->create();
    
    // Act: Make request as authenticated user
    $response = $this->actingAs($user)->get(route('route.name'));
    
    // Assert: Verify response structure and data
    $response->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('page/component')  // Verify correct component
            ->has('data.field')           // Verify data presence
            ->where('data.id', $expectedValue)  // Verify specific values
        );
}
```
</testing_setup>

### Common Testing Patterns with Reasoning

<testing_patterns>
**1. Component Assertion:**
```php
->assertInertia(fn (Assert $page) => $page
    ->component('uploads/index') // Verify correct component loads
)
// Why: Ensures proper routing and component mapping
```

**2. Data Structure Testing:**
```php
->assertInertia(fn (Assert $page) => $page
    ->has('uploads.data', 3) // Assert collection size
    ->has('uploads.data.0', fn (Assert $upload) => $upload
        ->has('id')      // Required fields
        ->has('title')
        ->has('status')
        ->etc()          // Allow additional fields
    )
)
// Why: Verifies data structure matches frontend expectations
```

**3. Specific Value Assertions:**
```php
->assertInertia(fn (Assert $page) => $page
    ->where('upload.data.id', $upload->id)
    ->where('filters.status', 'ready')
)
// Why: Confirms exact data values and filtering logic
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
// Why: Validates nested relationships and resource transformations
```
</testing_patterns>

### Controller-Specific Testing Examples

<controller_testing_examples>
**Upload Controller Testing with Reasoning:**
```php
// Index page with pagination and filtering
$response->assertOk()
    ->assertInertia(fn (Assert $page) => $page
        ->component('uploads/index')
        ->has('uploads.data')         // Collection data
        ->has('uploads.links')        // Pagination links
        ->has('uploads.meta')         // Pagination metadata
        ->has('filters')              // Current filter state
        ->has('filterOptions')        // Available filter options
    );
// Reasoning: Index pages need data, pagination, and filtering state

// Show page with resource data
$response->assertOk()
    ->assertInertia(fn (Assert $page) => $page
        ->component('uploads/show')
        ->has('upload.data', fn (Assert $upload) => $upload
            ->where('id', $upload->id)
            ->has('title')
            ->has('filename')
            ->has('user')              // Relationship loaded
            ->etc()
        )
    );
// Reasoning: Show pages need complete resource data with relationships
```

**Analysis Controller Testing:**
```php
// Analysis page with service status
$response->assertOk()
    ->assertInertia(fn (Assert $page) => $page
        ->component('uploads/analysis')
        ->has('upload.data')
        ->has('analysis_service', fn (Assert $service) => $service
            ->has('enabled')           // Service configuration
            ->has('available')         // Service availability
        )
    );
// Reasoning: Analysis pages need both upload data and service status
```
</controller_testing_examples>

### Testing Considerations with Explanations

<testing_considerations>
**Resource Wrapping:**
- Laravel resources wrap data in `.data` property
- Always use `upload.data` not `upload` for resource assertions
- Pagination data includes `.links` and `.meta` properties
- Why: Laravel API resources follow this structure for consistency

**Factory Hooks:**
- Be aware of model factory `afterCreating` hooks
- Use `make()` then `save()` to bypass hooks when needed
- Use `state(['field' => 'value'])` to override defaults
- Why: Factory hooks can create unexpected side effects in tests

**Authentication:**
- Always use `$this->actingAs($user)` for protected routes
- Test authorization with different users when applicable
- Why: Ensures proper access control and authorization logic

**Data Types:**
- Be precise with numeric types (int vs float)
- Use exact values for assertions (`->where('id', 1)`)
- Why: Type mismatches can cause test failures and indicate bugs
</testing_considerations>

### Testing Best Practices with Reasoning

<testing_best_practices>
1. **Test Component and Data Together**: Always verify both the correct component loads and contains expected data
   - Why: Ensures full-stack integration works correctly

2. **Use Nested Assertions**: Structure assertions to match your resource/component hierarchy  
   - Why: Mirrors actual data structure used by frontend components

3. **Test Edge Cases**: Include authorization, validation, and error scenarios
   - Why: Edge cases often reveal bugs not caught by happy path testing

4. **Mock External Services**: Use fakes for storage, queues, and external APIs
   - Why: Prevents external dependencies from causing test failures

5. **Verify Relationships**: Test that related data (user, analysis) is properly loaded
   - Why: Missing relationships cause frontend errors
</testing_best_practices>

### Example Test File Structure

<test_file_structure>
```php
class UploadControllerTest extends TestCase
{
    use RefreshDatabase;

    #[Test]
    public function index_requires_authentication() 
    { 
        // Test: Unauthenticated access redirects
        $response = $this->get(route('uploads.index'));
        $response->assertRedirect(route('login'));
    }
    
    #[Test] 
    public function index_returns_proper_inertia_response() 
    { 
        // Test: Authenticated access shows proper page structure
        $user = User::factory()->create();
        $uploads = Upload::factory()->count(3)->create(['user_id' => $user->id]);
        
        $response = $this->actingAs($user)->get(route('uploads.index'));
        
        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/index')
                ->has('uploads.data', 3)
            );
    }
    
    #[Test]
    public function show_returns_proper_inertia_response() 
    { 
        // Test: Show page displays upload with relationships
        $user = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $user->id]);
        
        $response = $this->actingAs($user)->get(route('uploads.show', $upload));
        
        $response->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('uploads/show')
                ->has('upload.data.user')
            );
    }
    
    #[Test]
    public function show_requires_upload_authorization() 
    { 
        // Test: Users can only view their own uploads
        $user = User::factory()->create();
        $otherUser = User::factory()->create();
        $upload = Upload::factory()->create(['user_id' => $otherUser->id]);
        
        $response = $this->actingAs($user)->get(route('uploads.show', $upload));
        $response->assertForbidden();
    }
}
```
</test_file_structure>

This testing approach ensures that your Inertia.js application works correctly across the full stack, from Laravel controllers to React components.

## Laravel Boost Integration Guidelines

<boost_integration>
**Laravel Boost is an MCP server with powerful tools designed specifically for this application.**

### Tool Usage Priority:
1. **Primary**: Use Laravel Boost tools first
2. **Secondary**: Fall back to standard tools only when Boost tools don't meet needs
3. **Documentation**: Always search Boost docs before other approaches
</boost_integration>

### Laravel Boost Tool Categories

<boost_tools>
**Artisan Commands**:
- Use `list-artisan-commands` tool when you need to call an Artisan command to double-check available parameters
- Why: Ensures correct parameter usage and discovers new options

**URL Generation**:
- Use `get-absolute-url` tool when sharing project URLs with users
- Why: Ensures correct scheme, domain/IP, and port configuration

**Development & Debugging**:
- Use `tinker` tool when you need to execute PHP to debug code or query Eloquent models directly
- Use `database-query` tool when you only need to read from the database
- Why: Direct access to application context and database

**Browser Debugging**:
- Use `browser-logs` tool to read browser logs, errors, and exceptions
- Only recent browser logs are useful - ignore old logs
- Why: Essential for debugging frontend issues

**Documentation Search**:
- Use `search-docs` tool before any other approaches
- Automatically passes installed packages and versions for version-specific results
- Perfect for Laravel ecosystem packages: Laravel, Inertia, Livewire, Filament, Tailwind, Pest, Nova
- Why: Returns accurate, version-specific documentation
</boost_tools>

### Documentation Search Best Practices

<docs_search_practices>
**Search Strategy**:
- Use multiple, broad, simple, topic-based queries to start
- Example: `['rate limiting', 'routing rate limiting', 'routing']`
- Search documentation before making code changes

**Available Search Syntax**:
1. **Simple Word Searches**: `query=authentication` - finds 'authenticate' and 'auth' with auto-stemming
2. **Multiple Words (AND Logic)**: `query=rate limit` - finds content with both "rate" AND "limit"
3. **Quoted Phrases (Exact Position)**: `query="infinite scroll"` - words must be adjacent and in order
4. **Mixed Queries**: `query=middleware "rate limit"` - "middleware" AND exact phrase "rate limit"
5. **Multiple Queries**: `queries=["authentication", "middleware"]` - ANY of these terms
</docs_search_practices>

## Framework-Specific Implementation Guidelines

### Inertia + Laravel Core Patterns

<inertia_laravel_patterns>
**Component Location**: Place Inertia.js components in `resources/js/Pages` directory unless specified differently in vite.config.js

**Server-Side Rendering**: Use `Inertia::render()` for server-side routing instead of traditional Blade views

<example_inertia_render>
```php
// routes/web.php example - Preferred approach
Route::get('/users', function () {
    return Inertia::render('Users/Index', [
        'users' => User::all()
    ]);
});

// Reasoning: Integrates Laravel routing with React components
```
</example_inertia_render>
</inertia_laravel_patterns>

### Inertia v2 Feature Usage

<inertia_v2_features>
**New Features Available:**
- **Polling**: For real-time data updates
- **Prefetching**: For improved perceived performance
- **Deferred props**: For lazy loading expensive data
- **Infinite scrolling**: Using merging props and `WhenVisible`
- **Lazy loading**: Data on scroll

**Implementation Rule**: Check documentation before implementing features to ensure correct v2 approach

**Deferred Props & Empty States**: When using deferred props, add animated skeleton states for better UX
</inertia_v2_features>

### Laravel Development Standards

<laravel_standards>
**File Creation**: Use `php artisan make:` commands to create new files
- Pass `--no-interaction` to ensure non-interactive execution
- Use `list-artisan-commands` tool to verify available options

**Database Operations**:
- Always use proper Eloquent relationship methods with return type hints
- Prefer relationship methods over raw queries or manual joins
- Avoid `DB::`; prefer `Model::query()`
- Generate code that prevents N+1 query problems using eager loading
- Use Laravel's query builder only for very complex database operations

**Model Creation Process**:
- When creating models, create useful factories and seeders too
- Ask user about additional needs using `list-artisan-commands`

**API Development**:
- Default to Eloquent API Resources and API versioning
- Follow existing application conventions if they differ

**Form Validation**:
- Always create Form Request classes rather than inline validation
- Include both validation rules and custom error messages
- Check sibling Form Requests for array vs string rule format

**Background Processing**:
- Use queued jobs with `ShouldQueue` interface for time-consuming operations

**Authentication & Authorization**:
- Use Laravel's built-in features (gates, policies, Sanctum)

**URL Generation**:
- Prefer named routes and `route()` function for links

**Configuration Management**:
- Use environment variables only in config files
- Never use `env()` function outside of config files
- Always use `config('app.name')`, not `env('APP_NAME')`
</laravel_standards>

### Laravel 12 Specific Patterns

<laravel_12_patterns>
**File Structure Changes**:
- No middleware files in `app/Http/Middleware/`
- Register middleware in `bootstrap/app.php`
- Service providers in `bootstrap/providers.php`
- Console configuration in `bootstrap/app.php` or `routes/console.php`
- Commands auto-register from `app/Console/Commands/` directory

**Database Operations**:
- When modifying columns, include all previously defined attributes to prevent data loss
- Use native eager loading limits: `$query->latest()->limit(10)`

**Model Patterns**:
- Use `casts()` method instead of `$casts` property when possible
- Follow existing project conventions
</laravel_12_patterns>

### Code Formatting Requirements

<formatting_requirements>
**Laravel Pint**:
- Must run `vendor/bin/pint --dirty` before finalizing changes
- Do not run `vendor/bin/pint --test`, use `vendor/bin/pint` to fix issues
- Why: Ensures consistent code style across the project
</formatting_requirements>

### Inertia + React Implementation

<inertia_react_implementation>
**Navigation**: Use `router.visit()` or `<Link>` for navigation

<example_navigation>
```typescript
import { Link } from '@inertiajs/react'

// Correct approach
<Link href="/">Home</Link>

// Why: Maintains SPA experience with server-side routing
```
</example_navigation>

**Form Handling**: Use `router.post` and related methods, not regular forms

<example_form_handling>
```typescript
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

// Why: Integrates with Laravel validation and Inertia's form handling
```
</example_form_handling>
</inertia_react_implementation>

### Tailwind CSS Implementation

<tailwind_implementation>
**Core Principles**:
- Use Tailwind CSS classes for styling
- Check existing project conventions before creating new patterns
- Extract repeated patterns into components matching project conventions
- Think through class placement, order, priority, and defaults
- Remove redundant classes and group elements logically

**Spacing Rules**:
- Use gap utilities for list item spacing, avoid margins

<example_spacing>
```html
<!-- Correct approach -->
<div class="flex gap-8">
    <div>Superior</div>
    <div>Michigan</div>
    <div>Erie</div>
</div>

<!-- Why: Gap utilities provide consistent spacing without margin conflicts -->
```
</example_spacing>

**Dark Mode Support**:
- If existing components support dark mode, new components must use similar patterns
- Typically implement using `dark:` prefix classes
</tailwind_implementation>

### Tailwind v4 Specific Requirements

<tailwind_v4_requirements>
**Import Method**:
```css
/* Correct v4 approach */
@import "tailwindcss";

/* Avoid v3 directives */
/* @tailwind base;
   @tailwind components; 
   @tailwind utilities; */
```

**Replaced Utilities** (use replacement, not deprecated):
- `bg-opacity-*` → `bg-black/*`
- `text-opacity-*` → `text-black/*`
- `border-opacity-*` → `border-black/*`
- `flex-shrink-*` → `shrink-*`
- `flex-grow-*` → `grow-*`
- `overflow-ellipsis` → `text-ellipsis`

**Removed Features**:
- `corePlugins` not supported in v4
- Opacity values remain numeric
</tailwind_v4_requirements>

### Testing Standards

<testing_standards>
**Test Requirement**: Every change must be programmatically tested
- Write new test or update existing test
- Run affected tests to ensure they pass
- Use `php artisan test` with specific filename or filter for efficiency

**Testing Best Practices**:
- Use model factories for test data creation
- Check for custom factory states before manual setup
- Use `$this->faker->word()` or `fake()->randomDigit()` following project conventions
- Create feature tests by default, use `--unit` flag only when needed
</testing_standards>

### Filament v4 Admin Panel Standards

<filament_v4_standards>
**Version**: Uses Filament v4.0.3 as admin panel backend system

**Creation Commands**: Always use `php artisan make:filament-resource` and related commands

**Structure Requirements**:
- Admin URL: `/admin` with separate authentication
- Resources in `app/Filament/Resources/`
- Component organization: dedicated subdirectories for Pages, Tables, Schemas, RelationManagers

**Resource Development Process**:
- Use `make:filament-resource Model --generate` for scaffolding
- Follow pattern: Resource class + Pages + Tables + Schemas
- Use existing custom components when available:
  - `AudioPlayerEntry`: For audio playback
  - `ProcessingStatusEntry`: For upload processing status
  - `FileSizeEntry`: For formatted file size display

**Development Standards**:
- Follow existing directory structure and naming conventions
- Use QueryBuilder filters for complex data filtering
- Implement proper Laravel policy authorization
- Use RelationManagers for related data instead of separate resources when appropriate
- Leverage built-in Filament features before building custom solutions
</filament_v4_standards>

## Error Handling and Debugging

<error_handling>
**Vite Manifest Error**: If you encounter "Unable to locate file in Vite manifest" error:
1. Run `npm run build` to generate manifest
2. Or ask user to run `npm run dev` or `composer run dev`
3. Why: Vite needs to generate manifest file for asset resolution
</error_handling>

## Service Layer Architecture & Decision Framework

The application uses a comprehensive service layer for external integrations and complex business logic.

### Service Selection Decision Tree

<service_selection_framework>
**Choose service based on operation type:**

**Audio Processing Operations:**
- `AudioConversionService`: FFmpeg operations, format conversion
- `AudioAnalysisService`: Microservice integration, analysis workflows
- `AudioMicroserviceClient`: Direct HTTP communication with analysis API
- `AudioMicroserviceMigrationService`: Database migration and cleanup operations

**Storage Operations:**
- `R2StorageService`: Cloudflare R2 bucket operations, file management
- Use when: Working with cloud storage, file uploads, public/private bucket management

**Decision Process:**
1. **Identify Operation Domain**: Audio processing vs Storage vs Migration
2. **Check Dependencies**: Does operation require external services?
3. **Consider Error Handling**: Does operation need retry logic?
4. **Evaluate Complexity**: Simple operations use models directly, complex use services
</service_selection_framework>

### Service Architecture Patterns

<service_patterns>
**Service Dependency Chain:**
```
Controller → Service → Client/External API
     ↓         ↓           ↓
  Request   Business    External
 Handling    Logic     Integration
```

**Error Handling Pattern:**
- Services throw domain-specific exceptions
- Controllers catch and transform to HTTP responses
- Background jobs handle service failures with retries

**Service Method Categories:**
1. **Synchronous Operations**: Direct API calls, immediate results
2. **Asynchronous Operations**: Job dispatch, status tracking
3. **Status Operations**: Check progress, validate states
4. **Cleanup Operations**: Delete tasks, clear resources
</service_patterns>

### Service Usage Examples

<service_usage_examples>
**AudioAnalysisService Usage Pattern:**
```php
// Controller usage - async operation
public function startAnalysis(Upload $upload)
{
    try {
        $taskId = $this->audioAnalysisService->submitForAnalysis($upload);
        return redirect()->back()->with('success', 'Analysis started');
    } catch (ServiceException $e) {
        return redirect()->back()->with('error', $e->getMessage());
    }
}

// Job usage - status checking
public function handle()
{
    $status = $this->audioAnalysisService->checkTaskStatus($this->taskId);
    
    if ($status['completed']) {
        $results = $this->audioAnalysisService->fetchAnalysisResults($this->taskId);
        // Process results
    } else {
        // Re-queue for later checking
        CheckAnalysisTaskStatus::dispatch($this->taskId)->delay(now()->addMinutes(2));
    }
}
```

**R2StorageService Usage Pattern:**
```php
// Upload file to R2
$path = $this->r2StorageService->uploadFile($file, 'bucket-name', 'path/file.ext');

// Download file from R2 to local temp
$tempPath = $this->r2StorageService->downloadToTemp('bucket-name', 'path/file.ext');

// Publish file (make publicly accessible)
$publicUrl = $this->r2StorageService->publishFile('private-bucket', 'public-bucket', 'path/file.ext');
```
</service_usage_examples>

## Job Orchestration & Queue Management Patterns

The application uses sophisticated job orchestration for multi-step audio processing workflows.

### Job Classification Framework

<job_classification>
**Job Types by Purpose:**

**Primary Processing Jobs:**
- `ProcessAudioUpload`: Main audio conversion and publishing
- `ConvertAndPublishAudio`: R2-specific conversion workflow
- When: File format conversion, initial processing

**Status Checking Jobs:**
- `CheckAnalysisTaskStatus`: Monitor analysis progress
- `CheckStemTaskStatus`: Monitor stem separation progress  
- When: Long-running external operations, periodic status updates

**Publishing Jobs:**
- `PublishToPublicBucket`: Move files from private to public R2 buckets
- When: Making processed files publicly accessible

**Decision Criteria:**
1. **Processing Duration**: Long operations need status checking jobs
2. **External Dependencies**: External APIs require status monitoring
3. **Error Recovery**: Complex workflows need retry-able sub-jobs
4. **Resource Management**: Memory-intensive operations need isolation
</job_classification>

### Job Orchestration Patterns

<job_orchestration>
**Chain Pattern - Sequential Processing:**
```php
// Primary job dispatches follow-up jobs
ProcessAudioUpload::dispatch($upload)
    ->chain([
        new PublishToPublicBucket($upload),
        new NotifyUploadComplete($upload)
    ]);
```

**Status Polling Pattern - External Service Integration:**
```php
// Job dispatches itself for status checking
public function handle()
{
    $status = $this->checkExternalService();
    
    if ($status->isComplete()) {
        $this->processResults($status->getResults());
    } else if ($status->isFailed()) {
        $this->handleFailure($status->getError());
    } else {
        // Re-queue with delay
        static::dispatch($this->taskId)
            ->delay(now()->addMinutes($this->getPollingInterval()));
    }
}
```

**Fan-Out Pattern - Parallel Processing:**
```php
// Dispatch multiple independent jobs
foreach ($upload->getProcessingTypes() as $type) {
    match($type) {
        'analysis' => CheckAnalysisTaskStatus::dispatch($upload),
        'stems' => CheckStemTaskStatus::dispatch($upload),
        'tempo' => CheckTempoTaskStatus::dispatch($upload),
    };
}
```
</job_orchestration>

### Queue Configuration Strategy

<queue_strategy>
**Queue Separation by Characteristics:**

**High Priority Queue (default):**
- User-initiated uploads
- Real-time status updates
- Interactive operations

**Low Priority Queue (bulk):**
- Background analysis tasks
- Status checking jobs
- Cleanup operations

**External Queue (external):**
- Operations dependent on external services
- Long timeout tolerances
- Separate failure handling

**Configuration Example:**
```php
// In Job classes
public $queue = 'external'; // For microservice-dependent jobs
public $tries = 5;          // Retry attempts
public $timeout = 600;      // 10 minutes timeout
public $backoff = [60, 120, 300]; // Progressive backoff
```
</queue_strategy>

## Event-Driven Processing Architecture

The application uses Laravel events for decoupled processing coordination and real-time updates.

### Event Classification & Usage

<event_classification>
**Event Types by Processing Stage:**

**Completion Events:**
- `UploadProcessed`: Basic audio conversion complete
- `AnalysisCompleted`: Analysis microservice task finished
- `StemSeparationCompleted`: Stem separation task finished
- `TempoProcessingCompleted`: Tempo processing task finished

**Usage Pattern:**
1. **Job completes successfully** → Fire event
2. **Event listeners** → Handle notifications, UI updates, follow-up actions
3. **Broadcasting** → Real-time UI updates via WebSockets

**Event-Driven Decision Tree:**
```
Job Success → Event → Listeners → Actions
     ↓           ↓         ↓         ↓
Processing   Domain    Business  UI Updates
Complete    Event     Logic     Broadcasting
```
</event_classification>

### Event-Listener Coordination

<event_coordination>
**Event Broadcasting Pattern:**
```php
// In Event class
class AnalysisCompleted implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public function __construct(
        public Upload $upload,
        public UploadAnalysis $analysis
    ) {}

    public function broadcastOn(): array
    {
        return [
            new PrivateChannel('upload.' . $this->upload->id),
        ];
    }
}

// In Job class  
public function handle()
{
    // Process analysis results
    $analysis = $this->processAnalysisResults();
    
    // Fire event for coordination
    AnalysisCompleted::dispatch($this->upload, $analysis);
}
```

**Multi-Listener Pattern:**
```php
// Event Service Provider
protected $listen = [
    AnalysisCompleted::class => [
        SendAnalysisNotification::class,
        UpdateAnalysisMetrics::class,
        TriggerSimilarTrackIndexing::class,
    ],
];
```

**Conditional Event Handling:**
```php
// Listener logic
public function handle(AnalysisCompleted $event)
{
    if ($event->analysis->hasMusicalFeatures()) {
        FindSimilarTracks::dispatch($event->upload);
    }
    
    if ($event->upload->user->wantsNotifications()) {
        SendAnalysisEmail::dispatch($event->upload->user, $event->analysis);
    }
}
```
</event_coordination>

## Advanced Model Relationship Patterns

The application uses sophisticated model relationships for multi-stage processing workflows.

### Task-Based Workflow Models

<task_workflow_models>
**Processing Workflow Pattern:**
Each processing type follows: Upload → Task → Results

```
Upload (1:1) UploadAnalysisTask (1:1) UploadAnalysis
Upload (1:1) UploadStemTask (1:m) UploadStems  
Upload (1:1) UploadTempoTask (1:m) UploadTempos
```

**Task Model Responsibilities:**
- **Task Models**: Track processing status, external task IDs, metadata
- **Result Models**: Store processed data, analysis results, generated files
- **Upload Model**: Coordinate access to all processing states

**Status Progression Pattern:**
```php
// Task status flow
'pending' → 'submitted' → 'processing' → 'completed'/'failed'

// Upload processing state methods
$upload->hasAnalysis()              // Analysis completed
$upload->isAnalysisInProgress()     // Analysis running
$upload->hasStems()                 // Stem separation completed
$upload->isStemSeparationInProgress() // Stem processing running
```
</task_workflow_models>

### Multi-Stage Processing Relationships

<multi_stage_processing>
**Dependent Processing Chain:**
```php
// Upload model methods coordinate complex state
public function canStartStemSeparation(): bool
{
    return $this->status === 'ready' && 
           $this->hasAnalysis() && 
           !$this->isStemSeparationInProgress();
}

public function canStartTempoProcessing(): bool
{
    return $this->hasAnalysis() && 
           $this->analysis->hasBpmData();
}

// Controller logic uses model state methods
public function startStemSeparation(Upload $upload)
{
    if (!$upload->canStartStemSeparation()) {
        return redirect()->back()
            ->with('error', 'Upload not ready for stem separation');
    }
    
    $this->audioAnalysisService->submitForStemSeparation($upload);
}
```

**Storage Strategy by Processing Type:**
```php
// Upload model handles different storage patterns
public function getAnalysisFileUrl(): ?string
{
    return $this->hasAnalysis() 
        ? $this->analysis->getPublicUrl() 
        : null;
}

public function getStemUrls(): array
{
    return $this->stems->mapWithKeys(function ($stem) {
        return [$stem->type => $stem->getPublicUrl()];
    })->toArray();
}

public function getTempoUrls(): array
{
    return $this->tempos->mapWithKeys(function ($tempo) {
        return [$tempo->preset_name => $tempo->getPublicUrl()];
    })->toArray();
}
```
</multi_stage_processing>

## Console Command Architecture Guidelines

The application uses custom Artisan commands for system management, diagnostics, and data migrations.

### Command Classification Framework

<command_classification>
**Command Categories by Purpose:**

**System Management Commands:**
- `ClearUploadStorage`: Remove all upload files, reset storage state
- `MigrateFreshWithMicroservice`: Complete system reset including external services
- When: Development environment setup, system maintenance

**Migration Commands:**
- `MigrateAudioMicroservice`: Database migration with external service coordination
- `MigrateUploadsToR2`: Move existing files from local to cloud storage
- When: Infrastructure changes, storage migration

**Diagnostic Commands:**
- `TempoProcessingDiagnostic`: Debug tempo processing issues
- When: Troubleshooting, system health checks

**Command Design Patterns:**
1. **Atomic Operations**: Commands should be safe to re-run
2. **Progress Reporting**: Long-running commands show progress
3. **Confirmation Prompts**: Destructive operations require confirmation
4. **Error Recovery**: Commands handle partial completion gracefully
</command_classification>

### Command Implementation Patterns

<command_patterns>
**Safe Operation Pattern:**
```php
public function handle()
{
    if (!$this->option('force')) {
        if (!$this->confirm('This will delete all upload files. Continue?')) {
            $this->info('Operation cancelled.');
            return Command::SUCCESS;
        }
    }
    
    $this->info('Starting upload storage cleanup...');
    
    try {
        $deletedCount = $this->clearUploadStorage();
        $this->info("Deleted {$deletedCount} files successfully.");
        return Command::SUCCESS;
    } catch (Exception $e) {
        $this->error("Error: {$e->getMessage()}");
        return Command::FAILURE;
    }
}
```

**Progress Reporting Pattern:**
```php
public function handle()
{
    $uploads = Upload::where('storage_type', 'local')->get();
    $bar = $this->output->createProgressBar($uploads->count());
    
    foreach ($uploads as $upload) {
        try {
            $this->migrateUpload($upload);
            $bar->advance();
        } catch (Exception $e) {
            $this->warn("Failed to migrate upload {$upload->id}: {$e->getMessage()}");
        }
    }
    
    $bar->finish();
    $this->newLine();
}
```

**Service Integration Pattern:**
```php
public function handle()
{
    $this->info('Checking microservice connectivity...');
    
    if (!$this->audioAnalysisService->isServiceAvailable()) {
        $this->error('Microservice not available.');
        return Command::FAILURE;
    }
    
    $this->info('Running migration...');
    $result = $this->audioMicroserviceMigrationService->migrate(
        type: $this->option('type'),
        force: $this->option('force')
    );
    
    $this->table(['Operation', 'Status'], $result->toArray());
}
```
</command_patterns>

## Multi-Modal Audio Processing Framework

The application supports multiple types of audio processing with coordinated workflows.

### Processing Type Decision Framework

<processing_type_decisions>
**Processing Types & Capabilities:**

**Audio Analysis (Primary):**
- **Purpose**: Extract musical features (BPM, key, loudness, etc.)
- **Dependencies**: External microservice, upload ready status
- **Outputs**: UploadAnalysis with structured data
- **Prerequisites**: Upload status = 'ready'

**Stem Separation:**
- **Purpose**: Separate audio into bass, drums, vocals, other tracks
- **Dependencies**: Analysis completed (uses analysis metadata)
- **Outputs**: Multiple UploadStem records with audio files
- **Prerequisites**: hasAnalysis() = true

**Tempo Processing:**
- **Purpose**: Generate tempo-shifted versions at different speeds
- **Dependencies**: Analysis completed (uses BPM data)
- **Outputs**: Multiple UploadTempo records with speed variations
- **Prerequisites**: Analysis has BPM data

**Processing Decision Tree:**
```
Upload Ready → Analysis → Stems + Tempo Processing
     ↓            ↓            ↓
  Required    Optional     Optional
  First      Parallel    Parallel
```
</processing_type_decisions>

### Coordinated Processing Patterns

<coordinated_processing>
**Sequential Processing Pattern:**
```php
// Controller coordinates multi-stage processing
public function startCompleteProcessing(Upload $upload)
{
    // Always start with analysis
    $analysisTaskId = $this->audioAnalysisService->submitForAnalysis($upload);
    
    // Event listener will trigger dependent processing
    return redirect()->back()
        ->with('success', 'Complete processing started');
}

// Event listener coordinates dependent processing
public function handle(AnalysisCompleted $event)
{
    $upload = $event->upload;
    $analysis = $event->analysis;
    
    // Start stem separation if user requested
    if ($upload->user->prefersStemSeparation()) {
        $this->audioAnalysisService->submitForStemSeparation($upload);
    }
    
    // Start tempo processing if BPM available
    if ($analysis->hasBpmData()) {
        $this->audioAnalysisService->submitForTempoProcessing($upload);
    }
}
```

**Parallel Processing Coordination:**
```php
// Start multiple processing types simultaneously
public function startParallelProcessing(Upload $upload, array $types)
{
    $tasks = [];
    
    foreach ($types as $type) {
        $tasks[] = match($type) {
            'analysis' => $this->audioAnalysisService->submitForAnalysis($upload),
            'stems' => $this->audioAnalysisService->submitForStemSeparation($upload),
            'tempo' => $this->audioAnalysisService->submitForTempoProcessing($upload),
        };
    }
    
    return $tasks;
}
```

**Processing Status Coordination:**
```php
// Upload model provides unified status
public function getProcessingStatus(): array
{
    return [
        'analysis' => [
            'completed' => $this->hasAnalysis(),
            'in_progress' => $this->isAnalysisInProgress(),
            'available' => true,
        ],
        'stems' => [
            'completed' => $this->hasStems(),
            'in_progress' => $this->isStemSeparationInProgress(),
            'available' => $this->hasAnalysis(),
        ],
        'tempo' => [
            'completed' => $this->hasTempos(),
            'in_progress' => $this->isTempoProcessingInProgress(),
            'available' => $this->hasAnalysis(),
        ],
    ];
}
```
</coordinated_processing>

## Error Handling & Retry Strategies

The application implements comprehensive error handling for complex workflows involving external services.

### Error Classification Framework

<error_classification>
**Error Categories & Response Strategies:**

**Transient Errors (Retry):**
- Network timeouts, temporary service unavailability
- **Strategy**: Exponential backoff retry
- **Examples**: HTTP 503, connection timeouts

**Client Errors (Fail Fast):**
- Invalid requests, authentication failures
- **Strategy**: Immediate failure, user notification
- **Examples**: HTTP 400, 401, 403

**Resource Errors (Conditional Retry):**
- File not found, insufficient storage
- **Strategy**: Retry with resource validation
- **Examples**: Missing files, disk space

**Processing Errors (Graceful Degradation):**
- Analysis failures, conversion errors
- **Strategy**: Mark failed, preserve original
- **Examples**: Unsupported format, corrupted file

**Error Handling Decision Tree:**
```
Error Occurs → Classify → Strategy → Action
     ↓            ↓         ↓        ↓
Exception    Error Type  Response  Resolution
Thrown      Analysis   Strategy   Implementation
```
</error_classification>

### Service Error Handling Patterns

<service_error_handling>
**Service Exception Hierarchy:**
```php
// Base service exception
abstract class ServiceException extends Exception
{
    abstract public function isRetryable(): bool;
    abstract public function getRetryDelay(): int;
}

// Specific service exceptions
class MicroserviceUnavailableException extends ServiceException
{
    public function isRetryable(): bool { return true; }
    public function getRetryDelay(): int { return 300; } // 5 minutes
}

class InvalidUploadException extends ServiceException  
{
    public function isRetryable(): bool { return false; }
    public function getRetryDelay(): int { return 0; }
}
```

**Job Error Handling Pattern:**
```php
public function handle()
{
    try {
        $this->processUpload();
    } catch (ServiceException $e) {
        if ($e->isRetryable() && $this->attempts() < $this->tries) {
            $this->release($e->getRetryDelay());
            return;
        }
        
        $this->handlePermanentFailure($e);
        throw $e;
    }
}

private function handlePermanentFailure(ServiceException $e): void
{
    $this->upload->update(['status' => 'failed', 'error_message' => $e->getMessage()]);
    UploadProcessingFailed::dispatch($this->upload, $e);
}
```

**Controller Error Response Pattern:**
```php
public function startProcessing(Upload $upload)
{
    try {
        $taskId = $this->audioAnalysisService->submitForAnalysis($upload);
        return $this->successResponse('Processing started', ['task_id' => $taskId]);
    } catch (InvalidUploadException $e) {
        return $this->errorResponse('Invalid upload: ' . $e->getMessage(), 400);
    } catch (MicroserviceUnavailableException $e) {
        return $this->errorResponse('Service temporarily unavailable', 503);
    } catch (ServiceException $e) {
        Log::error('Unexpected service error', ['exception' => $e]);
        return $this->errorResponse('Processing failed', 500);
    }
}
```
</service_error_handling>

## Storage & Performance Patterns

The application uses hybrid storage strategies optimizing for performance and cost.

### Storage Strategy Decision Framework

<storage_strategy>
**Storage Type Selection:**

**Local Storage (storage/app):**
- **Use for**: Temporary files, processing intermediates
- **Advantages**: Fast access, no network latency
- **Disadvantages**: Server disk usage, not globally distributed

**R2 Private Buckets:**
- **Use for**: Original uploads, processing inputs
- **Advantages**: Unlimited storage, cost-effective
- **Disadvantages**: API rate limits, network latency

**R2 Public Buckets:**
- **Use for**: Streaming files, public access content
- **Advantages**: Direct browser access, CDN integration
- **Disadvantages**: Public exposure, bandwidth costs

**Decision Matrix:**
```
File Type    | Storage Location | Access Pattern | Public Access
-------------|------------------|----------------|---------------
Original     | R2 Private       | Rare          | No
Processing   | Local/Temp       | During job    | No
Stream       | R2 Public        | Frequent      | Yes
Analysis     | Database         | Frequent      | Via API
```
</storage_strategy>

### Performance Optimization Patterns

<performance_patterns>
**Lazy Loading Strategy:**
```php
// Model relationship optimization
public function analysis()
{
    return $this->hasOne(UploadAnalysis::class);
}

// Controller selective loading
public function show(Upload $upload)
{
    $upload->load([
        'user:id,name',
        'analysis' => function ($query) {
            $query->select(['upload_id', 'bpm', 'key', 'loudness']);
        }
    ]);
    
    return Inertia::render('Uploads/Show', [
        'upload' => new UploadResource($upload)
    ]);
}
```

**Caching Strategy:**
```php
// Model caching for expensive operations
public function getProcessingStatusAttribute(): array
{
    return Cache::remember(
        "upload.{$this->id}.processing_status",
        now()->addMinutes(5),
        fn () => $this->calculateProcessingStatus()
    );
}

// Service result caching
public function getServiceStatus(): array
{
    return Cache::remember(
        'audio_service_status',
        now()->addMinutes(2),
        fn () => $this->audioMicroserviceClient->checkHealth()
    );
}
```

**Queue Optimization:**
```php
// Job priority and delay strategies
public function startProcessing(Upload $upload)
{
    // High priority for small files
    if ($upload->size < 10 * 1024 * 1024) { // 10MB
        ProcessAudioUpload::dispatch($upload)->onQueue('high');
    } else {
        ProcessAudioUpload::dispatch($upload)
            ->onQueue('low')
            ->delay(now()->addMinutes(5)); // Delay large files
    }
}
```
</performance_patterns>

---

**Remember**: This guidance prioritizes accuracy, consistency, and following established patterns. Always use the decision frameworks and reasoning patterns outlined above when making development choices.