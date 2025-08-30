<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class EnsureSuperUser
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        // Check if user is authenticated
        if (! auth()->check()) {
            return redirect()->route('filament.admin.auth.login');
        }

        // Get the configured superuser role name
        $superUserRole = config('admin.superuser_role', 'SuperAdmin');

        // Check if user has SuperAdmin role
        if (! auth()->user()->hasRole($superUserRole)) {
            // Log unauthorized access attempt
            logger()->warning('Unauthorized admin panel access attempt - missing SuperUser role', [
                'user_id' => auth()->id(),
                'user_email' => auth()->user()->email,
                'ip' => $request->ip(),
                'user_agent' => $request->userAgent(),
                'url' => $request->fullUrl(),
                'timestamp' => now()->toISOString(),
                'required_role' => $superUserRole,
                'user_roles' => auth()->user()->roles->pluck('name')->toArray(),
            ]);

            // Return 404 to hide admin panel existence
            abort(404);
        }

        return $next($request);
    }
}
