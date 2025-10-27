<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Symfony\Component\HttpFoundation\Response;

class AdminRateLimiting
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $key = 'admin-access:'.$request->ip();
        $rateLimitConfig = config('admin.rate_limiting.global_requests', '60,1');

        // Handle malformed configuration gracefully
        $configParts = explode(',', $rateLimitConfig);
        if (count($configParts) !== 2) {
            // Fallback to default values if configuration is malformed
            $maxAttempts = 60;
            $decayMinutes = 1;
        } else {
            [$maxAttempts, $decayMinutes] = $configParts;
        }

        if (RateLimiter::tooManyAttempts($key, (int) $maxAttempts)) {
            $seconds = RateLimiter::availableIn($key);

            logger()->warning('Admin panel rate limit exceeded', [
                'ip' => $request->ip(),
                'user_agent' => $request->userAgent(),
                'url' => $request->fullUrl(),
                'retry_after' => $seconds,
                'timestamp' => now()->toISOString(),
            ]);

            // Return 404 instead of 429 to hide admin panel existence
            abort(404);
        }

        RateLimiter::hit($key, (int) $decayMinutes * 60);

        return $next($request);
    }
}
