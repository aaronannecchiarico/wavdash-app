<?php

use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('welcome');
})->name('home');

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('dashboard', function () {
        return Inertia::render('dashboard');
    })->name('dashboard');

    Route::resource('contests', \App\Http\Controllers\ContestController::class)
        ->only(['index'])
        ->names([
            'index' => 'contests.index',
        ]);

    Route::resource('uploads', \App\Http\Controllers\UploadController::class)
        ->parameters([
            'uploads' => 'upload'
        ]);
});

require __DIR__.'/settings.php';
require __DIR__.'/auth.php';
