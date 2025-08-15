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

    // Upload Analysis Routes (Web/Inertia)
    Route::prefix('uploads/{upload}/analysis')->name('uploads.analysis.')->group(function () {
        Route::post('/', [\App\Http\Controllers\UploadAnalysisController::class, 'store'])->name('store');
        Route::get('/', [\App\Http\Controllers\UploadAnalysisController::class, 'show'])->name('show');
        Route::delete('/', [\App\Http\Controllers\UploadAnalysisController::class, 'destroy'])->name('destroy');
        Route::delete('/task', [\App\Http\Controllers\UploadAnalysisController::class, 'deleteTask'])->name('delete-task');
        Route::get('/similar', [\App\Http\Controllers\UploadAnalysisController::class, 'similar'])->name('similar');
    });

    // Upload Stem Separation Routes (Web/Inertia)
    Route::prefix('uploads/{upload}/stems')->name('uploads.stems.')->group(function () {
        Route::post('/', [\App\Http\Controllers\UploadStemController::class, 'store'])->name('store');
        Route::get('/', [\App\Http\Controllers\UploadStemController::class, 'show'])->name('show');
        Route::delete('/', [\App\Http\Controllers\UploadStemController::class, 'destroy'])->name('destroy');
        Route::delete('/task', [\App\Http\Controllers\UploadStemController::class, 'deleteTask'])->name('delete-task');
        Route::get('/{stemType}/download', [\App\Http\Controllers\UploadStemController::class, 'downloadStem'])->name('download');
    });

    // Analysis service status (API)
    Route::get('api/analysis/status', [\App\Http\Controllers\UploadAnalysisController::class, 'status'])->name('analysis.status');
    
    // Stem separation service status (API)
    Route::get('api/stems/status', [\App\Http\Controllers\UploadStemController::class, 'status'])->name('stems.status');
});

require __DIR__.'/settings.php';
require __DIR__.'/auth.php';
