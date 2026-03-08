<?php

namespace App\Providers;

use Filament\Support\Facades\FilamentAsset;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Vite;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        Vite::prefetch(concurrency: 6);

        // Audio player is now loaded via CDN in AdminPanelProvider
        // No need for FilamentAsset registration

        // TEMP DEBUG: log all auth attempts
        Event::listen(\Illuminate\Auth\Events\Failed::class, function ($event) {
            logger()->error('Auth attempt FAILED', [
                'email' => $event->credentials['email'] ?? 'unknown',
                'guard' => $event->guard,
                'user_found' => $event->user !== null,
            ]);
        });
        Event::listen(\Illuminate\Auth\Events\Attempting::class, function ($event) {
            logger()->info('Auth attempt STARTED', [
                'credentials' => array_diff_key($event->credentials, ['password' => '']),
                'guard' => $event->guard,
            ]);
        });
    }
}
