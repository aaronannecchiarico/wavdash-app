<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Admin Panel Settings
    |--------------------------------------------------------------------------
    */
    'enabled' => env('ADMIN_PANEL_ENABLED', true),

    /*
    |--------------------------------------------------------------------------
    | IP Address Restrictions
    |--------------------------------------------------------------------------
    */
    'ip_whitelist' => [
        'enabled' => env('ADMIN_IP_RESTRICTION_ENABLED', true),
        'allowed_ips' => array_filter(explode(',', env('ADMIN_ALLOWED_IPS', '127.0.0.1,::1'))),
        'return_404_on_reject' => true,
    ],

    /*
    |--------------------------------------------------------------------------
    | SuperUser Settings
    |--------------------------------------------------------------------------
    */
    'superuser_role' => env('ADMIN_SUPERUSER_ROLE', 'SuperAdmin'),

    /*
    |--------------------------------------------------------------------------
    | Session Settings
    |--------------------------------------------------------------------------
    */
    'session_name' => env('ADMIN_SESSION_NAME', 'admin_session'),
    'session_lifetime' => env('ADMIN_SESSION_LIFETIME', 120), // minutes

    /*
    |--------------------------------------------------------------------------
    | Rate Limiting
    |--------------------------------------------------------------------------
    */
    'rate_limiting' => [
        'login_attempts' => env('ADMIN_LOGIN_RATE_LIMIT', '5,1'), // 5 attempts per minute
        'global_requests' => env('ADMIN_GLOBAL_RATE_LIMIT', '60,1'), // 60 requests per minute
    ],
];
