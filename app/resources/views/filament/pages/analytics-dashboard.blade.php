<x-filament-panels::page>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Upload Trends Chart -->
        <div class="col-span-1 lg:col-span-2">
            <x-filament::section
                heading="Monthly Upload Trends"
                description="Upload activity over the last 12 months"
                icon="heroicon-o-chart-bar"
            >
                <div class="h-64">
                    <canvas id="uploadTrendsChart" class="w-full h-full"></canvas>
                </div>
            </x-filament::section>
        </div>

        <!-- User Growth Chart -->
        <div>
            <x-filament::section
                heading="User Growth"
                description="Cumulative user registrations over time"
                icon="heroicon-o-users"
            >
                <div class="h-64">
                    <canvas id="userGrowthChart" class="w-full h-full"></canvas>
                </div>
            </x-filament::section>
        </div>

        <!-- Genre Distribution -->
        @if(count($genreStats) > 0)
        <div>
            <x-filament::section
                heading="Genre Distribution"
                description="Popular music genres on the platform"
                icon="heroicon-o-musical-note"
            >
                <div class="h-64">
                    <canvas id="genreStatsChart" class="w-full h-full"></canvas>
                </div>
            </x-filament::section>
        </div>
        @endif

        <!-- Top Contributors Widget -->
        <div class="col-span-1 lg:col-span-3">
            {{ $this->topContributorsInfolist }}
        </div>
    </div>

    @push('scripts')
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Upload Trends Chart
            const uploadTrendsCtx = document.getElementById('uploadTrendsChart').getContext('2d');
            new Chart(uploadTrendsCtx, {
                type: 'line',
                data: {
                    labels: @json($uploadTrends['labels']),
                    datasets: [{
                        label: 'Uploads',
                        data: @json($uploadTrends['data']),
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#f59e0b',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0, 0, 0, 0.1)' },
                            ticks: {
                                precision: 0,
                                font: { size: 11 },
                                maxTicksLimit: 5
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 11 },
                                maxRotation: 45
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });

            // User Growth Chart
            const userGrowthCtx = document.getElementById('userGrowthChart').getContext('2d');
            new Chart(userGrowthCtx, {
                type: 'line',
                data: {
                    labels: @json($userGrowth['labels']),
                    datasets: [{
                        label: 'Total Users',
                        data: @json($userGrowth['data']),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#3b82f6',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0, 0, 0, 0.1)' },
                            ticks: {
                                precision: 0,
                                font: { size: 11 },
                                maxTicksLimit: 5
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 10 },
                                maxRotation: 45
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });

            // Genre Stats Chart (only if canvas exists)
            const genreCanvas = document.getElementById('genreStatsChart');
            if (genreCanvas) {
                const genreStatsCtx = genreCanvas.getContext('2d');
                new Chart(genreStatsCtx, {
                    type: 'doughnut',
                    data: {
                        labels: @json($genreStats['labels']),
                        datasets: [{
                            data: @json($genreStats['data']),
                            backgroundColor: [
                                '#f59e0b', '#3b82f6', '#10b981', '#ef4444', '#8b5cf6',
                                '#f97316', '#06b6d4', '#84cc16', '#ec4899', '#6b7280'
                            ],
                            borderWidth: 2,
                            borderColor: '#fff',
                            hoverBorderWidth: 3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    padding: 15,
                                    usePointStyle: true,
                                    font: { size: 10 },
                                    boxWidth: 8,
                                    boxHeight: 8
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                borderColor: '#8b5cf6',
                                borderWidth: 1,
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.parsed || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return `${label}: ${value} (${percentage}%)`;
                                    }
                                }
                            }
                        },
                        cutout: '60%',
                        animation: {
                            animateRotate: true,
                            duration: 1000
                        }
                    }
                });
            }
        });
    </script>
    @endpush
</x-filament-panels::page>
