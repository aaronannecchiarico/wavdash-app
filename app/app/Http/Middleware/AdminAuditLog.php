<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class AdminAuditLog
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        // Log admin actions (excluding GET requests to reduce noise)
        if (! $request->isMethod('GET') && auth()->check()) {
            logger()->info('Admin action performed', [
                'user_id' => auth()->id(),
                'user_email' => auth()->user()->email,
                'action' => $request->method(),
                'url' => $request->fullUrl(),
                'ip' => $request->ip(),
                'user_agent' => $request->userAgent(),
                'timestamp' => now()->toISOString(),
                'response_status' => $response->getStatusCode(),
                'request_data' => $this->sanitizeRequestData($request),
            ]);
        }

        return $response;
    }

    /**
     * Sanitize request data for logging, removing sensitive information.
     */
    private function sanitizeRequestData(Request $request): array
    {
        $data = $request->all();

        // Remove sensitive fields
        $sensitiveFields = ['password', 'password_confirmation', 'token', '_token', 'api_key', 'secret'];

        foreach ($sensitiveFields as $field) {
            if (isset($data[$field])) {
                $data[$field] = '[REDACTED]';
            }
        }

        // Limit size to prevent excessive log entries
        $jsonData = json_encode($data);
        if (strlen($jsonData) > 2000) {
            return ['size_exceeded' => 'Request data too large for logging'];
        }

        return $data;
    }
}
