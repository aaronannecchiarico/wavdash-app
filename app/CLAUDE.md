# Claude Code Directives for Beat Forge

This document provides essential context for working on the **Beat Forge** repository, a Laravel 12, React, and Inertia.js application with a Filament v4 admin panel.

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

---

## 🏛️ Architecture & Core Concepts

### **Tech Stack**

* **Backend:** Laravel 12, Laravel Reverb (WebSockets)
* **Frontend:** React, Inertia.js v2, TypeScript, Tailwind CSS, Shadcn/ui
* **Admin Panel:** Filament v4
* **Database:** MySQL
* **Integrations:** Optional FastAPI audio analysis microservice, Cloudflare R2 for storage.

### **Key Data Flows**

1.  **Audio Processing:** User Upload → `ProcessAudioUpload` Job Queued → FFMpeg converts to OGG → `UploadProcessed` event broadcasted via Reverb → UI updates in real-time.
2.  **Data Rendering:** Laravel Controller (`Inertia::render()`) → Inertia.js Middleware → React Page Component (`/resources/js/Pages`).

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
* **Background Jobs:** Use the `ShouldQueue` interface for any time-consuming tasks like audio processing.
* **Code Style:** Run `vendor/bin/pint --dirty` to format your code before committing.

### **Frontend (Inertia.js & React)**

* **Routing & Navigation:**
    * All routes are defined in Laravel (`/routes/*.php`).
    * Use the `<Link>` component from `@inertiajs/react` for all internal navigation. **Do not use `<a>` tags.**
* **Data & Forms:**
    * Data is passed from Laravel controllers to React pages via `Inertia::render()`. **Avoid data fetching in `useEffect` hooks.**
    * Use the `useForm()` hook from `@inertiajs/react` to manage form state and submissions.
* **File Naming:** Use `kebab-case.tsx` for React components and hooks (e.g., `audio-player.tsx`).

### **Filament v4 Admin Panel**

* **Location:** The admin panel is accessed at the `/admin` route and has its own authentication.
* **File Generation:** Use `php artisan make:filament-resource` to create new resources, as it generates the complete file structure.
* **Component Usage:** Prefer built-in Filament components for forms, tables, and infolists. Only create custom components (like `AudioPlayerEntry`) when absolutely necessary.
* **Available Resources:** The panel manages `Users`, `Uploads`, `Contests`, and various analysis `Tasks`.

### **Testing (Pest & Inertia)**

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

* **`search-docs`**: Your first step for any question. It provides version-aware documentation for Laravel, Inertia, Filament, etc.
* **`list-artisan-commands`**: Use this to check the available parameters for any `artisan` command before running it.
* **`tinker` / `database-query`**: Use for direct debugging and data inspection.
* **`browser-logs`**: Essential for debugging frontend issues. Check recent logs first.
* **`get-absolute-url`**: Use to generate correct, shareable URLs for the application.
