<x-dynamic-component
    :component="$getEntryWrapperView()"
    :entry="$entry"
>
    <div class="h-64">
        <canvas id="genreStatsChart" class="w-full h-full"></canvas>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js not loaded');
                return;
            }
            
            // Only create chart if canvas exists and chart hasn't been created yet
            const canvas = document.getElementById('genreStatsChart');
            if (!canvas) return;
            
            // Destroy existing chart if it exists
            if (canvas.chart) {
                canvas.chart.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            canvas.chart = new Chart(ctx, {
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
        });
    </script>
</x-dynamic-component>