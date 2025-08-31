<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\IpUtils;
use Symfony\Component\HttpFoundation\Response;

class RestrictAdminByIP
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        // Skip IP check if disabled or in local environment
        if (! config('admin.ip_whitelist.enabled') || app()->environment('local')) {
            return $next($request);
        }

        $allowedIps = config('admin.ip_whitelist.allowed_ips', []);
        $clientIp = $request->ip();

        // Check if client IP is in allowed list (supports CIDR notation)
        $isAllowed = false;
        foreach ($allowedIps as $allowedIp) {
            if (IpUtils::checkIp($clientIp, $allowedIp)) {
                $isAllowed = true;
                break;
            }
        }

        if (! $isAllowed) {
            // Log unauthorized access attempt
            logger()->warning('Unauthorized admin panel access attempt', [
                'ip' => $clientIp,
                'user_agent' => $request->userAgent(),
                'url' => $request->fullUrl(),
                'timestamp' => now()->toISOString(),
            ]);

            // Return 404 to hide admin panel existence
            abort(404);
        }

        return $next($request);
    }
}
