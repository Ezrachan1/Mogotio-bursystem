// reports.js - External JavaScript for charts
document.addEventListener('DOMContentLoaded', function() {
    const reportDataElement = document.getElementById('reportData');
    const monthlyDataElement = document.getElementById('monthlyData');
    
    if (!reportDataElement || !monthlyDataElement) {
        console.log('No data available for charts');
        return;
    }
    
    const reportData = JSON.parse(reportDataElement.textContent);
    const monthlyApplications = JSON.parse(monthlyDataElement.textContent);
    
    // Status Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx && reportData.by_status) {
        const statusLabels = Object.keys(reportData.by_status).map(status => 
            status.charAt(0).toUpperCase() + status.slice(1)
        );
        const statusValues = Object.values(reportData.by_status);
        
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: statusLabels,
                datasets: [{
                    data: statusValues,
                    backgroundColor: [
                        '#6c757d', '#17a2b8', '#ffc107', '#6f42c1', 
                        '#28a745', '#dc3545', '#20c997'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Education Level Chart
    const educationCtx = document.getElementById('educationChart');
    if (educationCtx && reportData.by_education_level) {
        const educationLabels = Object.keys(reportData.by_education_level).map(level => 
            level.charAt(0).toUpperCase() + level.slice(1)
        );
        const educationValues = Object.values(reportData.by_education_level);
        
        new Chart(educationCtx, {
            type: 'bar',
            data: {
                labels: educationLabels,
                datasets: [{
                    label: 'Applications',
                    data: educationValues,
                    backgroundColor: '#0d6efd'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Monthly Trends Chart
    const trendsCtx = document.getElementById('trendsChart');
    if (trendsCtx && monthlyApplications) {
        const monthLabels = monthlyApplications.map(item => {
            const date = new Date(item.month);
            return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        });
        const monthValues = monthlyApplications.map(item => item.count);
        
        new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: 'Applications',
                    data: monthValues,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Set progress bar widths
    document.querySelectorAll('.progress-bar[data-width]').forEach(function(bar) {
        const width = bar.getAttribute('data-width');
        bar.style.width = width + '%';
    });
});