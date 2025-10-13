<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Admin Panel Settings
    |--------------------------------------------------------------------------
    |
    | Configuration for the Filament v4 admin panel (/admin route).
    | The admin panel provides management interfaces for users, uploads,
    | contests, and various analysis tasks.
    |
    */
    'enabled' => env('ADMIN_PANEL_ENABLED', true),

    /*
    |--------------------------------------------------------------------------
    | IP Address Restrictions
    |--------------------------------------------------------------------------
    |
    | Security: Restrict admin panel access to specific IP addresses.
    | In production, configure ADMIN_ALLOWED_IPS with your team's IPs.
    | Format: Comma-separated list (e.g., "192.168.1.1,10.0.0.5")
    | IPv6 supported: ::1 is localhost for IPv6
    |
    */
    'ip_whitelist' => [
        'enabled' => env('ADMIN_IP_RESTRICTION_ENABLED', true),
        'allowed_ips' => array_filter(explode(',', env('ADMIN_ALLOWED_IPS', '127.0.0.1,::1'))),
        'return_404_on_reject' => true, // Return 404 instead of 403 for security
    ],

    /*
    |--------------------------------------------------------------------------
    | SuperUser Settings
    |--------------------------------------------------------------------------
    |
    | Define the role name that grants unrestricted admin panel access.
    | Users with this role bypass all permission checks.
    |
    */
    'superuser_role' => env('ADMIN_SUPERUSER_ROLE', 'SuperAdmin'),

    /*
    |--------------------------------------------------------------------------
    | Session Settings
    |--------------------------------------------------------------------------
    |
    | Admin panel uses a separate session from the main application for
    | enhanced security. Session lifetime is in minutes.
    |
    */
    'session_name' => env('ADMIN_SESSION_NAME', 'admin_session'),
    'session_lifetime' => env('ADMIN_SESSION_LIFETIME', 120), // minutes

    /*
    |--------------------------------------------------------------------------
    | Rate Limiting
    |--------------------------------------------------------------------------
    |
    | Protect admin panel from brute force attacks with rate limiting.
    | Format: "max_attempts,decay_minutes"
    | Example: "5,1" = 5 attempts per 1 minute
    |
    */
    'rate_limiting' => [
        'login_attempts' => env('ADMIN_LOGIN_RATE_LIMIT', '5,1'), // 5 attempts per minute
        'global_requests' => env('ADMIN_GLOBAL_RATE_LIMIT', '60,1'), // 60 requests per minute
    ],
];
