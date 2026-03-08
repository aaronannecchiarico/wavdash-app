<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    |
    | This file is for storing the credentials for third party services such
    | as Mailgun, Postmark, AWS and more. This file provides the de facto
    | location for this type of information, allowing packages to have
    | a conventional file to locate the various service credentials.
    |
    */

    'postmark' => [
        'token' => env('POSTMARK_TOKEN'),
    ],

    'ses' => [
        'key' => env('AWS_ACCESS_KEY_ID'),
        'secret' => env('AWS_SECRET_ACCESS_KEY'),
        'region' => env('AWS_DEFAULT_REGION', 'us-east-1'),
    ],

    'resend' => [
        'key' => env('RESEND_KEY'),
    ],

    'slack' => [
        'notifications' => [
            'bot_user_oauth_token' => env('SLACK_BOT_USER_OAUTH_TOKEN'),
            'channel' => env('SLACK_BOT_USER_DEFAULT_CHANNEL'),
        ],
    ],

    'audio_analysis' => [
        'base_url' => env('AUDIO_ANALYSIS_BASE_URL', 'http://localhost:8001'),
        // Internal URL used for callback URLs sent to the audio service.
        // Must be reachable from inside the audio service container.
        // Defaults to APP_URL if not set.
        'callback_base_url' => env('AUDIO_CALLBACK_BASE_URL', env('APP_URL')),
        'enabled' => env('AUDIO_ANALYSIS_ENABLED', true),
        'r2_integration_enabled' => env('AUDIO_ANALYSIS_R2_ENABLED', true),
        'migration_timeout' => env('AUDIO_ANALYSIS_MIGRATION_TIMEOUT', 60), // 1 minute
    ],

];
