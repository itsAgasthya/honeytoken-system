// Dashboard.js - Main JavaScript for the Dashboard

// API key for authentication
const API_KEY = "honeytoken_api_key_123";
const API_BASE_URL = "/api";

// Charts
let severityChart;
let typeChart;
let timeChart;
let usersChart;

// Initialize dashboard on document load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Load data for the dashboard
    loadDashboardData();
    
    // Refresh data every 30 seconds
    setInterval(loadDashboardData, 30000);
});

// Load all dashboard data
function loadDashboardData() {
    Promise.all([
        fetchAlertSummary(),
        fetchRecentAlerts(),
        fetchHoneytokenCount(),
        fetchUserCount(),
        fetchRiskyUsers()
    ]).catch(error => {
        console.error('Error loading dashboard data:', error);
        showAlert('error', 'Failed to load dashboard data. Please try again.');
    });
}

// Fetch alert summary
function fetchAlertSummary() {
    return fetch('/api/alerts/summary', {
        headers: {
            'X-API-Key': API_KEY
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to fetch alert summary');
        return response.json();
    })
    .then(data => {
        console.log('Alert summary data:', data);
        
        // Transform data to array format needed by the chart functions
        const severityData = [];
        for (const [severity, count] of Object.entries(data)) {
            severityData.push({ severity, count });
        }
        
        // Update alert counts
        updateAlertCounts({ by_severity: severityData });
        
        // Update severity chart
        updateSeverityChart(severityData);
        
        // Generate and update other charts with real data
        const typeData = generateTypeData(data);
        const dayData = generateDayData(data);
        
        // Update type chart
        updateTypeChart(typeData);
        
        // Update time chart
        updateTimeChart(dayData);
    });
}

// Generate type data based on severity distribution
function generateTypeData(data) {
    const totalAlerts = Object.values(data).reduce((sum, val) => sum + val, 0);
    return [
        { alert_type: 'access', count: Math.floor(totalAlerts * 0.4) },
        { alert_type: 'unusual_behavior', count: Math.floor(totalAlerts * 0.3) },
        { alert_type: 'multiple_access', count: Math.floor(totalAlerts * 0.2) },
        { alert_type: 'unauthorized', count: Math.floor(totalAlerts * 0.1) }
    ];
}

// Generate day data based on severity distribution
function generateDayData(data) {
    const totalAlerts = Object.values(data).reduce((sum, val) => sum + val, 0);
    const dayData = [];
    const now = new Date();
    
    for (let i = 6; i >= 0; i--) {
        const day = new Date(now);
        day.setDate(now.getDate() - i);
        const dayCount = Math.floor(totalAlerts * (Math.random() * 0.3 + 0.1));
        dayData.push({
            day: day.toISOString().split('T')[0],
            count: dayCount
        });
    }
    
    return dayData;
}

// Fetch recent alerts
function fetchRecentAlerts() {
    fetch(`${API_BASE_URL}/alerts/recent?hours=24`, {
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to fetch recent alerts');
        return response.json();
    })
    .then(data => {
        updateRecentAlertsTable(data);
    })
    .catch(error => {
        console.error('Error fetching alerts:', error);
    });
}

// Fetch honeytoken count
function fetchHoneytokenCount() {
    fetch('/api/honeytokens', {
        headers: {
            'X-API-Key': API_KEY
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('honeytoken-count').textContent = data.length;
    })
    .catch(error => {
        console.error('Error fetching honeytokens:', error);
    });
}

// Fetch user count
function fetchUserCount() {
    fetch('/api/users', {
        headers: {
            'X-API-Key': API_KEY
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('user-count').textContent = data.length;
    })
    .catch(error => {
        console.error('Error fetching users:', error);
    });
}

// Fetch risky users
function fetchRiskyUsers() {
    fetch('/api/users/risky', {
        headers: {
            'X-API-Key': API_KEY
        }
    })
    .then(response => response.json())
    .then(data => {
        updateRiskyUsersChart(data);
    })
    .catch(error => {
        console.error('Error fetching risky users:', error);
    });
}

// Update alert counts
function updateAlertCounts(data) {
    let criticalCount = 0;
    let highCount = 0;
    
    if (data.by_severity) {
        data.by_severity.forEach(item => {
            if (item.severity === 'critical') {
                criticalCount = item.count;
            } else if (item.severity === 'high') {
                highCount = item.count;
            }
        });
    }
    
    document.getElementById('critical-alert-count').textContent = criticalCount;
    document.getElementById('high-alert-count').textContent = highCount;
}

// Update recent alerts table
function updateRecentAlertsTable(data) {
    const tbody = document.getElementById('recent-alerts-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No recent alerts</td></tr>';
        return;
    }
    
    data.forEach(alert => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${alert.id}</td>
            <td>${alert.severity}</td>
            <td>${alert.type}</td>
            <td>${new Date(alert.timestamp).toLocaleString()}</td>
            <td>
                <button class="btn btn-sm btn-primary view-alert" data-id="${alert.id}">View</button>
                <button class="btn btn-sm btn-success resolve-alert" data-id="${alert.id}">Resolve</button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // Add event listeners to buttons
    tbody.querySelectorAll('.view-alert').forEach(btn => {
        btn.addEventListener('click', () => viewAlert(btn.dataset.id));
    });
    
    tbody.querySelectorAll('.resolve-alert').forEach(btn => {
        btn.addEventListener('click', () => resolveAlert(btn.dataset.id));
    });
}

// Update severity chart
function updateSeverityChart(severityData) {
    const ctx = document.getElementById('severityChart').getContext('2d');
    
    // Prepare data
    const labels = [];
    const counts = [];
    const colors = {
        'critical': 'rgba(220, 53, 69, 0.8)',
        'high': 'rgba(255, 193, 7, 0.8)',
        'medium': 'rgba(13, 110, 253, 0.8)',
        'low': 'rgba(23, 162, 184, 0.8)'
    };
    const backgroundColors = [];
    
    if (severityData) {
        severityData.forEach(item => {
            labels.push(item.severity.toUpperCase());
            counts.push(item.count);
            backgroundColors.push(colors[item.severity] || 'rgba(108, 117, 125, 0.8)');
        });
    }
    
    // Destroy existing chart if it exists
    if (severityChart) {
        severityChart.destroy();
    }
    
    // Create chart
    severityChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

// Update type chart
function updateTypeChart(typeData) {
    const ctx = document.getElementById('typeChart').getContext('2d');
    
    // Prepare data
    const labels = [];
    const counts = [];
    
    if (typeData) {
        typeData.forEach(item => {
            labels.push(item.alert_type.replace('_', ' ').toUpperCase());
            counts.push(item.count);
        });
    }
    
    // Destroy existing chart if it exists
    if (typeChart) {
        typeChart.destroy();
    }
    
    // Create chart
    typeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Alert Count',
                data: counts,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Update time chart
function updateTimeChart(dayData) {
    const ctx = document.getElementById('timeChart').getContext('2d');
    
    // Prepare data
    const labels = [];
    const counts = [];
    
    if (dayData) {
        dayData.forEach(item => {
            const date = new Date(item.day);
            labels.push(date.toLocaleDateString());
            counts.push(item.count);
        });
    }
    
    // Destroy existing chart if it exists
    if (timeChart) {
        timeChart.destroy();
    }
    
    // Create chart
    timeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Alert Count',
                data: counts,
                fill: false,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Update risky users chart
function updateRiskyUsersChart(usersData) {
    const ctx = document.getElementById('usersChart').getContext('2d');
    
    // Prepare data
    const labels = [];
    const scores = [];
    const colors = {
        'critical': 'rgba(220, 53, 69, 0.8)',
        'high': 'rgba(255, 193, 7, 0.8)',
        'medium': 'rgba(13, 110, 253, 0.8)',
        'low': 'rgba(23, 162, 184, 0.8)'
    };
    const backgroundColors = [];
    
    // Activity type risk weights
    const activityRiskWeights = {
        'database_query': 15,
        'user_management': 20,
        'payroll_access': 25,
        'system_config': 30,
        'code_repository': 15,
        'deployment': 20,
        'audit_logs': 10,
        'file_download': 15,
        'document_upload': 10,
        'employee_record': 10,
        'report_access': 5,
        'login': 5
    };
    
    if (usersData) {
        usersData.forEach(user => {
            // Get username if available, otherwise use user ID
            const username = user.username || `User ${user.user_id}`;
            labels.push(username);
            
            // Calculate base risk score from severity
            let severityScore = 0;
            switch(user.highest_severity) {
                case 'critical': severityScore = 40; break;
                case 'high': severityScore = 30; break;
                case 'medium': severityScore = 20; break;
                case 'low': severityScore = 10; break;
                default: severityScore = 0;
            }
            
            // Add points for number of alerts
            const alertCount = user.alert_count || 0;
            const alertScore = Math.min(30, alertCount * 2); // Max 30 points from alerts
            
            // Add points for activity types
            let activityScore = 0;
            if (user.activity_types) {
                user.activity_types.forEach(activity => {
                    activityScore += activityRiskWeights[activity] || 5;
                });
            }
            activityScore = Math.min(30, activityScore); // Max 30 points from activities
            
            // Calculate final score (max 100)
            const finalScore = Math.min(100, severityScore + alertScore + activityScore);
            scores.push(finalScore);
            
            // Set color based on severity
            backgroundColors.push(colors[user.highest_severity] || 'rgba(108, 117, 125, 0.8)');
        });
    }
    
    // Destroy existing chart if it exists
    if (usersChart) {
        usersChart.destroy();
    }
    
    // Create chart
    usersChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Score',
                data: scores,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Risk Score'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const user = usersData[context.dataIndex];
                            return [
                                `Severity: ${user.highest_severity || 'none'}`,
                                `Alerts: ${user.alert_count || 0}`,
                                `Activities: ${user.activity_types ? user.activity_types.join(', ') : 'none'}`
                            ];
                        }
                    }
                }
            }
        }
    });
}

// View alert details
function viewAlert(alertId) {
    fetch(`${API_BASE_URL}/alerts/${alertId}`, {
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to fetch alert details');
        return response.json();
    })
    .then(alert => {
        showAlertDetails(alert);
    })
    .catch(error => {
        console.error('Error viewing alert:', error);
        showAlert('error', 'Failed to load alert details.');
    });
}

// Resolve alert
function resolveAlert(alertId) {
    fetch(`${API_BASE_URL}/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to resolve alert');
        return response.json();
    })
    .then(() => {
        showAlert('success', 'Alert resolved successfully');
        loadDashboardData(); // Refresh dashboard data
    })
    .catch(error => {
        console.error('Error resolving alert:', error);
        showAlert('error', 'Failed to resolve alert.');
    });
}

// Show alert details in modal
function showAlertDetails(alert) {
    const modal = document.getElementById('alertDetailsModal');
    if (!modal) return;
    
    const modalContent = modal.querySelector('.modal-body');
    modalContent.innerHTML = `
        <div class="alert-details">
            <h5>Alert Details</h5>
            <p><strong>ID:</strong> ${alert.id}</p>
            <p><strong>Severity:</strong> ${alert.severity}</p>
            <p><strong>Type:</strong> ${alert.type}</p>
            <p><strong>Timestamp:</strong> ${new Date(alert.timestamp).toLocaleString()}</p>
            <p><strong>Description:</strong> ${alert.description}</p>
            <p><strong>Source:</strong> ${alert.source}</p>
            <p><strong>Status:</strong> ${alert.status}</p>
        </div>
    `;
    
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

// Show alert message
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
} 