# Claude Code Directives for WavDash

This document provides essential context for working on the **WavDash** repository, a Laravel 12, React, and Inertia.js application with a Filament v4 admin panel.

---

## 🚀 Key Commands & Workflows

This is your primary reference for common tasks. Commands are organized by workflow.

### **Development**

* **Full Stack (Recommended):** `composer run dev`
    * Starts the Laravel server, queue worker, logs, and Vite dev server. **Use this for most tasks.**
* **Fresh Start:** `php artisan migrate:fresh-with-microservice --seed`
    * **Complete system reset.** Wipes and reseeds the Laravel DB, microservice DB, and all storage. Use when starting a major new feature or after schema changes.
* **Frontend Only:** `npm run dev`
    * Runs the Vite dev server only. Use for UI changes that don't need the backend.
* **SSR Development:** `composer run dev:ssr`
    * Use when working on or testing server-side rendering features.

### **Testing & Validation**

* **Run All Tests:** `composer run test`
* **Run a Specific Test:** `php artisan test tests/Feature/SpecificTest.php`
* **Code Formatting (Fix):** `vendor/bin/pint --dirty`
    * **Run this before finalizing changes.** It automatically formats modified PHP files.
* **Frontend Linting:** `npm run lint`
* **Frontend Type Checking:** `npm run types`

### **Database & Storage**

* **Apply New Migrations:** `php artisan migrate`
* **Reset Laravel DB Only:** `php artisan migrate:fresh --seed`
    * Resets the main database but preserves the microservice and storage state.
* **Clear Upload Storage:** `php artisan uploads:clear --force`

### **Services & Integrations**

* **Reset Audio Microservice:** `php artisan audio:migrate --type=fresh --force`
* **List Cloudflare R2 Buckets:** `npx wrangler r2 bucket list`
* **List Objects in R2 Bucket:** `npx wrangler r2 object list <bucket-name>`

### **Marketing Site Integration**

* **Local Development:** The Astro marketing site runs on `http://localhost:4321` by default
* **Production:** Marketing site is at `https://wavdash.com`, app is at `https://app.wavdash.com`
* **Home Route Behavior:** Visiting `/` redirects to marketing site if logged out, or dashboard if logged in
* **Configuration:** Set `MARKETING_URL` in `.env` to configure the marketing site URL
* **Related Docs:** See `/docs/MARKETING_AUTH_SHARING.md` for complete implementation guide

---

## 🏛️ Architecture & Core Concepts

### **Tech Stack**

* **Backend:** Laravel 12, Laravel Reverb (WebSockets)
* **Frontend:** React, Inertia.js v2, TypeScript, Tailwind CSS, Shadcn/ui
* **Admin Panel:** Filament v4
* **Database:** MySQL
* **Marketing Site:** Astro (separate repository, handles public-facing pages)
* **Integrations:** Optional FastAPI audio analysis microservice, Cloudflare R2 for storage.

### **Key Data Flows**

1.  **Audio Processing (Client-Side):** User Upload → MediaBunny processes to OGG on client → Direct upload to storage → Immediate `UploadProcessed` event → UI updates instantly.
2.  **Data Rendering:** Laravel Controller (`Inertia::render()`) → Inertia.js Middleware → React Page Component (`/resources/js/Pages`).
3.  **Stems Processing:** Uses server-side `AudioConversionService` and `ConvertAndPublishAudio` job for advanced audio analysis features.
4.  **Cross-Domain Authentication:** Marketing site (Astro) → `/api/auth/check` endpoint → Laravel session cookies → Display login state → Route to appropriate page.

### **Important Directory Structures**

* **Laravel Models:** `/app/Models/`
* **Laravel Jobs/Events:** `/app/Jobs/`, `/app/Events/`
* **Filament Resources:** `/app/Filament/Resources/` (contains subdirectories for Pages, Schemas, Tables, etc.)
* **React Pages:** `/resources/js/Pages/`
* **React Components:** `/resources/js/components/`
* **Type Definitions:** `/resources/js/types/`

---

## 📝 Development Patterns & Best Practices

Follow these patterns to maintain code consistency and quality.

### **Backend (Laravel)**

* **Configuration:** Register Service Providers in `bootstrap/providers.php` and Middleware in `bootstrap/app.php`.
* **Validation:** **Always use Form Request classes** instead of inline validation in controllers.
* **Database:**
    * Use Eloquent relationships and eager loading (`with()`) to prevent N+1 queries.
    * Prefer `Model::query()` over the `DB::` facade.
* **File Creation:** Use `php artisan make:` commands to generate boilerplate for models, controllers, etc.
* **Background Jobs:** Use the `ShouldQueue` interface for time-consuming tasks like stems processing. **Note:** `ProcessAudioUpload` job is deprecated in Phase 4 - main upload processing now happens client-side.
* **Code Style:** Run `vendor/bin/pint --dirty` to format your code before committing.

### **Frontend (Inertia.js & React)**

* **Routing & Navigation:**
    * All routes are defined in Laravel (`/routes/*.php`).
    * Use the `<Link>` component from `@inertiajs/react` for all internal navigation. **Do not use `<a>` tags.**
* **Data & Forms:**
    * Data is passed from Laravel controllers to React pages via `Inertia::render()`. **Avoid data fetching in `useEffect` hooks.**
    * Use the `useForm()` hook from `@inertiajs/react` to manage form state and submissions.
* **File Naming:** Use `kebab-case.tsx` for React components and hooks (e.g., `audio-player.tsx`).

### **Neobrutalism Component Library**

* **Primary UI Library:** For the neobrutalist redesign, use components from https://neobrutalism.dev
* **Component Location:** Neobrutalism components are installed in `/resources/js/components/ui/neo/`
* **Installation:** Use `npx shadcn@latest add https://neobrutalism.dev/r/[component].json` to install components
* **CSS Variables Only:** Neobrutalism components use CSS variables, not utility classes
* **Styling System:** Uses custom CSS variables defined in `resources/css/app.css` adapted to WavDash brand colors
* **Preferred Usage:** For redesign work, prefer neobrutalism components over standard shadcn/ui components

### **Client-Side Audio Processing (Phase 4)**

* **MediaBunny Library:** Uses MediaBunny for client-side audio conversion to OGG Opus format
* **Hook Location:** `useClientAudioProcessing` in `/resources/js/hooks/useClientAudioProcessing.ts`
* **Browser Support:** Requires WebCodecs API support (Chrome, Edge, modern browsers)
* **Processing Flow:** File validation → MediaBunny conversion → Direct upload with metadata
* **Error Handling:** User-friendly error messages with fallback suggestions
* **Required Fields:** Client-processed uploads must include `client_processed=true`, `original_filename`, `original_size`, and `duration`
* **Server Fallback:** **Deprecated in Phase 4** - server-side processing is no longer supported for main uploads

### **Filament v4 Admin Panel**

* **Location:** The admin panel is accessed at the `/admin` route and has its own authentication.
* **File Generation:** Use `php artisan make:filament-resource` to create new resources, as it generates the complete file structure.
* **Component Usage:** Prefer built-in Filament components for forms, tables, and infolists. Only create custom components (like `AudioPlayerEntry`) when absolutely necessary.
* **Available Resources:** The panel manages `Users`, `Uploads`, `Contests`, and various analysis `Tasks`.

### **Testing (PHPUnit & Inertia)**

* **Core Assertion:** The primary tool for testing is `assertInertia`.
* **Test Structure:**
    1.  **Arrange:** Set up data using factories (`User::factory()->create()`).
    2.  **Act:** Make a request as an authenticated user (`$this->actingAs($user)->get(...)`).
    3.  **Assert:** Verify the response, component, and data structure.
* **Key Assertions:**
    * `->component('Page/Component')`: Ensures the correct React component is loaded.
    * `->has('prop.data')`: Checks for the existence and structure of data.
    * `->where('prop.data.id', $value)`: Verifies specific data values.
* **Example Test Snippet:**

    ```php
    use Inertia\Testing\AssertableInertia as Assert;

    // ...

    $response = $this->actingAs($user)->get(route('uploads.show', $upload));

    $response->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('uploads/show')
            ->has('upload.data', fn (Assert $prop) => $prop
                ->where('id', $upload->id)
                ->has('user') // Assert relationship is loaded
                ->etc()
            )
        );
    ```

---

## 🛠️ Specialized Tooling (Laravel Boost)

This project is integrated with Laravel Boost. **Always prioritize Boost tools.**

| Name                       | Notes                                                                                                          |
| -------------------------- |----------------------------------------------------------------------------------------------------------------|
| Application Info           | Read PHP & Laravel versions, database engine, list of ecosystem packages with versions, and Eloquent models    |
| Browser Logs               | Read logs and errors from the browser                                                                          |
| Database Connections       | Inspect available database connections, including the default connection                                       |
| Database Query             | Execute a query against the database                                                                           |
| Database Schema            | Read the database schema                                                                                       |
| Get Absolute URL           | Convert relative path URIs to absolute so agents generate valid URLs                                           |
| Get Config                 | Get a value from the configuration files using "dot" notation                                                  |
| Last Error                 | Read the last error from the application's log files                                                           |
| List Artisan Commands      | Inspect the available Artisan commands                                                                         |
| List Available Config Keys | Inspect the available configuration keys                                                                       |
| List Available Env Vars    | Inspect the available environment variable keys                                                                |
| List Routes                | Inspect the application's routes                                                                               |
| Read Log Entries           | Read the last N log entries                                                                                    |
| Report Feedback            | Share Boost & Laravel AI feedback with the team, just say "give Boost feedback: x, y, and z"                   |
| Search Docs                | Query the Laravel hosted documentation API service to retrieve documentation based on installed packages       |
| Tinker                     | Execute arbitrary code within the context of the application                                                   |

## Tooling for shell interactions 

- Is it about finding FILES? use `fd` 
- Is it about finding TEXT/strings? use `rg` 
- Is it about finding CODE STRUCTURE? use `ast-grep` https://ast-grep.github.io/llms.txt 
- Is it about SELECTING from multiple results? pipe to `zf` 
- Is it about interacting with JSON? use `jq` 
- Is it about interacting with YAML or XML? use `yq`
