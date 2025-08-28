<x-filament-panels::page>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Upload Trends Chart -->
        <div class="col-span-1 lg:col-span-2">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow duration-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white">Monthly Upload Trends</h3>
                    <div class="flex items-center space-x-2">
                        <div class="w-3 h-3 bg-amber-400 rounded-full"></div>
                        <span class="text-sm text-gray-500 dark:text-gray-400">Last 12 months</span>
                    </div>
                </div>
                <div class="h-48">
                    <canvas id="uploadTrendsChart" class="w-full h-full"></canvas>
                </div>
            </div>
        </div>

        <!-- User Growth Chart -->
        <div>
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow duration-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-base font-medium text-gray-900 dark:text-white">User Growth</h3>
                    <div class="flex items-center space-x-2">
                        <div class="w-3 h-3 bg-blue-400 rounded-full"></div>
                        <span class="text-sm text-gray-500 dark:text-gray-400">Cumulative</span>
                    </div>
                </div>
                <div class="h-48">
                    <canvas id="userGrowthChart" class="w-full h-full"></canvas>
                </div>
            </div>
        </div>

        <!-- Genre Distribution -->
        <div>
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow duration-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-base font-medium text-gray-900 dark:text-white">Genre Distribution</h3>
                    <div class="flex items-center space-x-2">
                        <div class="w-3 h-3 bg-purple-400 rounded-full"></div>
                        <span class="text-sm text-gray-500 dark:text-gray-400">Top 10</span>
                    </div>
                </div>
                <div class="h-48">
                    <canvas id="genreStatsChart" class="w-full h-full"></canvas>
                </div>
            </div>
        </div>

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
                        legend: {
                            display: false
                        },
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
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                precision: 0,
                                font: { size: 11 },
                                maxTicksLimit: 5
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
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
                        legend: {
                            display: false
                        },
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
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                precision: 0,
                                font: { size: 11 },
                                maxTicksLimit: 5
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
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

            // Genre Stats Chart
            @if(count($genreStats['labels']) > 0)
            const genreStatsCtx = document.getElementById('genreStatsChart').getContext('2d');
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
            @else
            // Show empty state for genre chart
            const genreStatsCtx = document.getElementById('genreStatsChart').getContext('2d');
            genreStatsCtx.fillStyle = '#9ca3af';
            genreStatsCtx.font = '14px Arial';
            genreStatsCtx.textAlign = 'center';
            genreStatsCtx.fillText('No genre data available', genreStatsCtx.canvas.width / 2, genreStatsCtx.canvas.height / 2);
            @endif
        });
    </script>
    @endpush
</x-filament-panels::page>
