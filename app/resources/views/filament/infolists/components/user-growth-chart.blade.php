<x-dynamic-component
    :component="$getEntryWrapperView()"
    :entry="$entry"
>
    <div class="h-64">
        <canvas id="userGrowthChart" class="w-full h-full"></canvas>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js not loaded');
                return;
            }
            
            // Only create chart if canvas exists and chart hasn't been created yet
            const canvas = document.getElementById('userGrowthChart');
            if (!canvas) return;
            
            // Destroy existing chart if it exists
            if (canvas.chart) {
                canvas.chart.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            canvas.chart = new Chart(ctx, {
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
        });
    </script>
</x-dynamic-component>