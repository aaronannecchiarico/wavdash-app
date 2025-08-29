<?php

namespace App\Providers\Filament;

use Filament\Auth\MultiFactor\App\AppAuthentication;
use Filament\Auth\MultiFactor\Email\EmailAuthentication;
use Filament\Http\Middleware\Authenticate;
use Filament\Http\Middleware\AuthenticateSession;
use Filament\Http\Middleware\DisableBladeIconComponents;
use Filament\Http\Middleware\DispatchServingFilamentEvent;
use Filament\Pages\Dashboard;
use Filament\Panel;
use Filament\PanelProvider;
use Filament\Support\Colors\Color;
use Filament\Widgets\AccountWidget;
use Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse;
use Illuminate\Cookie\Middleware\EncryptCookies;
use Illuminate\Foundation\Http\Middleware\VerifyCsrfToken;
use Illuminate\Routing\Middleware\SubstituteBindings;
use Illuminate\Session\Middleware\StartSession;
use Illuminate\View\Middleware\ShareErrorsFromSession;
use Resma\FilamentAwinTheme\FilamentAwinTheme;

class AdminPanelProvider extends PanelProvider
{
    public function panel(Panel $panel): Panel
    {
        return $panel
            ->default()
            ->id('admin')
            ->path('admin')
            ->login()
            ->profile()
            ->multiFactorAuthentication([
                AppAuthentication::make()
                    ->recoverable()
                    ->recoveryCodeCount(8),
                EmailAuthentication::make(),
            ])
            ->strictAuthorization()
            ->plugins([
                FilamentAwinTheme::make(),
            ])
            ->colors([
                'primary' => Color::Amber,
            ])
            ->discoverResources(in: app_path('Filament/Resources'), for: 'App\\Filament\\Resources')
            ->discoverPages(in: app_path('Filament/Pages'), for: 'App\\Filament\\Pages')
            ->pages([
                Dashboard::class,
            ])
            ->discoverWidgets(in: app_path('Filament/Widgets'), for: 'App\\Filament\\Widgets')
            ->widgets([
                AccountWidget::class,
                \App\Filament\Widgets\UploadStatsOverview::class,
                \App\Filament\Widgets\SystemHealthOverview::class,
                \App\Filament\Widgets\UploadsChart::class,
                \App\Filament\Widgets\UserActivityOverview::class,
            ])
            ->renderHook(
                'panels::head.end',
                fn (): string => '
                <script src="https://unpkg.com/wavesurfer.js@7"></script>
                <script>
                    document.addEventListener("alpine:init", () => {
                        Alpine.data("audioPlayer", ({ audioUrl, title = null, duration = null }) => ({
                            wavesurfer: null,
                            isPlaying: false,
                            isLoading: true,
                            error: null,

                            init() {
                                console.log("Inline audio player init", audioUrl);
                                
                                if (typeof WaveSurfer === "undefined") {
                                    this.error = "WaveSurfer not loaded";
                                    this.isLoading = false;
                                    return;
                                }
                                
                                this.$nextTick(() => {
                                    this.initWaveSurfer();
                                });
                            },

                            initWaveSurfer() {
                                try {
                                    if (!this.$refs.waveform) {
                                        throw new Error("No waveform container");
                                    }

                                    this.wavesurfer = WaveSurfer.create({
                                        container: this.$refs.waveform,
                                        waveColor: "#e5e7eb",
                                        progressColor: "#3b82f6",
                                        height: 60,
                                        responsive: true,
                                    });

                                    this.wavesurfer.load(audioUrl);

                                    this.wavesurfer.on("ready", () => {
                                        console.log("WaveSurfer ready");
                                        this.isLoading = false;
                                    });

                                    this.wavesurfer.on("play", () => {
                                        this.isPlaying = true;
                                    });

                                    this.wavesurfer.on("pause", () => {
                                        this.isPlaying = false;
                                    });

                                    this.wavesurfer.on("error", (error) => {
                                        console.error("WaveSurfer error:", error);
                                        this.error = "Audio load error";
                                        this.isLoading = false;
                                    });
                                } catch (error) {
                                    console.error("Init error:", error);
                                    this.error = error.message;
                                    this.isLoading = false;
                                }
                            },

                            togglePlayPause() {
                                console.log("Toggle clicked");
                                if (!this.wavesurfer) {
                                    this.error = "Player not ready";
                                    return;
                                }
                                
                                if (this.isPlaying) {
                                    this.wavesurfer.pause();
                                } else {
                                    this.wavesurfer.play();
                                }
                            }
                        }));
                    });
                </script>
            '
            )
            ->middleware([
                EncryptCookies::class,
                AddQueuedCookiesToResponse::class,
                StartSession::class,
                AuthenticateSession::class,
                ShareErrorsFromSession::class,
                VerifyCsrfToken::class,
                SubstituteBindings::class,
                DisableBladeIconComponents::class,
                DispatchServingFilamentEvent::class,
            ])
            ->authMiddleware([
                Authenticate::class,
            ]);
    }
}
