<?php

use App\Http\Controllers\Api\AudioAnalysisCallbackController;
use App\Http\Controllers\Api\AuthController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "api" middleware group. Make something great!
|
*/

// Authentication check endpoint (uses 'web' middleware for session support)
Route::middleware('web')->group(function () {
    Route::get('/auth/check', [AuthController::class, 'check']);
});

// Audio Analysis Callbacks (no auth required for microservice callbacks)
Route::prefix('audio/analysis')->name('api.audio.analysis.')->group(function () {
    // Analysis completion callback from microservice
    Route::post('callback/{upload}', [AudioAnalysisCallbackController::class, 'handleAnalysisCallback'])
        ->name('callback');

    // Stem separation callback from microservice
    Route::post('stems/callback/{upload}', [AudioAnalysisCallbackController::class, 'handleStemCallback'])
        ->name('stems.callback');

    // R2 storage status endpoint for microservice health checks
    Route::get('r2/status', [AudioAnalysisCallbackController::class, 'r2Status'])
        ->name('r2.status');
});
