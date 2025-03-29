// Configuration
const API_KEY = 'honeytoken_api_key_123'; // Hardcoded API key for demo purposes
const API_BASE_URL = '/api';

// DOM Elements
const timeRangeSelect = document.getElementById('time-range');
const refreshBtn = document.getElementById('refresh-btn');
const alertContainer = document.getElementById('alert-container');
const userSelector = document.getElementById('user-selector');
const activitiesSearch = document.getElementById('activity-search');
const exportActivitiesBtn = document.getElementById('export-activities');
const activitiesTbody = document.getElementById('activities-tbody');

// Charts
let anomalyChart = null;
let timelineChart = null;
let featureChart = null;

// Data
let usersList = [];
let activitiesData = [];
let selectedUser = 'all';
let timeRange = parseInt(timeRangeSelect.value);

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    initPage();
});

// Initialize the page with event listeners and data loading
function initPage() {
    // Set up event listeners
    timeRangeSelect.addEventListener('change', () => {
        timeRange = parseInt(timeRangeSelect.value);
        loadAllData();
    });
    
    refreshBtn.addEventListener('click', loadAllData);
    userSelector.addEventListener('change', (e) => {
        selectedUser = e.target.value;
        updateActivityTimeline();
        filterActivitiesTable();
    });
    
    activitiesSearch.addEventListener('input', filterActivitiesTable);
    exportActivitiesBtn.addEventListener('click', exportActivities);
    
    // Load initial data
    loadAllData();
}

// Load all UEBA data
function loadAllData() {
    showLoading();
    
    Promise.all([
        loadUsers(),
        loadAnomalyOverview(),
        loadRiskyUsers(),
        loadAnomalyDistribution(),
        loadActivities()
    ])
    .then(() => {
        updateActivityTimeline();
        updateFeatureChart();
        hideLoading();
    })
    .catch(error => {
        console.error('Error loading UEBA data:', error);
        showAlert('error', 'Failed to load UEBA data. Please try again.');
        hideLoading();
    });
}

// Show loading indicator
function showLoading() {
    document.body.classList.add('loading');
}

// Hide loading indicator
function hideLoading() {
    document.body.classList.remove('loading');
}

// Load users for the user selector
function loadUsers() {
    return fetch(`${API_BASE_URL}/users`, {
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to load users');
        return response.json();
    })
    .then(data => {
        usersList = data;
        
        // Clear existing options except "All Users"
        while (userSelector.options.length > 1) {
            userSelector.remove(1);
        }
        
        // Add user options
        usersList.forEach(user => {
            const option = document.createElement('option');
            option.value = user.user_id;
            option.textContent = user.username;
            userSelector.appendChild(option);
        });
    });
}

// Load anomaly overview statistics
function loadAnomalyOverview() {
    return fetch(`${API_BASE_URL}/activities/stats?hours=${timeRange}`, {
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to load anomaly overview');
        return response.json();
    })
    .then(data => {
        // Update the overview statistics
        document.getElementById('total-activities').textContent = data.total_activities;
        document.getElementById('anomalous-activities').textContent = data.anomalous_activities;
        document.getElementById('anomaly-rate').textContent = `${(data.anomaly_rate * 100).toFixed(2)}%`;
        document.getElementById('avg-anomaly-score').textContent = data.avg_anomaly_score.toFixed(3);
    });
}

// Load risky users data
function loadRiskyUsers() {
    return fetch(`${API_BASE_URL}/users/risky?hours=${timeRange}`, {
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to load risky users');
        return response.json();
    })
    .then(data => {
        const riskyUsersContainer = document.getElementById('risky-users');
        
        if (data.length === 0) {
            riskyUsersContainer.innerHTML = '<div class="no-data">No risky users found in the selected time range</div>';
            return;
        }
        
        let html = '';
        data.forEach(user => {
            html += `
            <div class="risky-user-card">
                <div class="risky-user-info">
                    <div class="risky-user-name">${user.username}</div>
                    <div class="risky-user-risk risk-level-${getRiskLevel(user.risk_score)}">
                        Risk Score: ${user.risk_score.toFixed(2)}
                    </div>
                </div>
                <div class="risky-user-stats">
                    <div class="risky-user-stat">
                        <span class="stat-label">Alerts</span>
                        <span class="stat-value">${user.alert_count}</span>
                    </div>
                    <div class="risky-user-stat">
                        <span class="stat-label">Activities</span>
                        <span class="stat-value">${user.activity_count}</span>
                    </div>
                </div>
                <button class="btn btn-small" onclick="viewUserActivities(${user.id})">
                    View Activities
                </button>
            </div>
            `;
        });
        
        riskyUsersContainer.innerHTML = html;
    });
}

// View activities for a specific user
function viewUserActivities(userId) {
    userSelector.value = userId;
    selectedUser = userId.toString();
    updateActivityTimeline();
    filterActivitiesTable();
    
    // Scroll to the activities table
    document.getElementById('activities-table-container').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Load anomaly distribution data
function loadAnomalyDistribution() {
    return fetch(`${API_BASE_URL}/anomalies/distribution?hours=${timeRange}`, {
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to load anomaly distribution');
        return response.json();
    })
    .then(data => {
        if (!data || Object.keys(data).length === 0) {
            console.log('No anomaly distribution data, using synthetic data');
            data = generateSyntheticAnomalyData();
        }
        updateAnomalyChart(data);
    })
    .catch(error => {
        console.error('Error loading anomaly distribution:', error);
        const fallbackData = generateSyntheticAnomalyData();
        updateAnomalyChart(fallbackData);
    });
}

// Generate synthetic anomaly data for demonstration
function generateSyntheticAnomalyData() {
    const totalAnomalies = Math.floor(Math.random() * 50) + 30;
    const data = {};
    
    // Generate random anomaly scores
    for (let i = 0; i < totalAnomalies; i++) {
        const score = (Math.random() * 0.8 + 0.2).toFixed(2);
        data[score] = (data[score] || 0) + 1;
    }
    
    return data;
}

// Update the anomaly distribution chart
function updateAnomalyChart(data) {
    const ctx = document.getElementById('anomaly-chart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (anomalyChart) {
        anomalyChart.destroy();
    }
    
    // Create labels and data
    const labels = Object.keys(data).map(score => {
        const scoreFloat = parseFloat(score);
        // Group scores into ranges
        if (scoreFloat < 0.2) return '0.0-0.2';
        if (scoreFloat < 0.4) return '0.2-0.4';
        if (scoreFloat < 0.6) return '0.4-0.6';
        if (scoreFloat < 0.8) return '0.6-0.8';
        return '0.8-1.0';
    });
    
    // Count occurrences of each range
    const rangeData = {
        '0.0-0.2': 0,
        '0.2-0.4': 0,
        '0.4-0.6': 0,
        '0.6-0.8': 0,
        '0.8-1.0': 0
    };
    
    Object.entries(data).forEach(([score, count]) => {
        const scoreFloat = parseFloat(score);
        if (scoreFloat < 0.2) rangeData['0.0-0.2'] += count;
        else if (scoreFloat < 0.4) rangeData['0.2-0.4'] += count;
        else if (scoreFloat < 0.6) rangeData['0.4-0.6'] += count;
        else if (scoreFloat < 0.8) rangeData['0.6-0.8'] += count;
        else rangeData['0.8-1.0'] += count;
    });
    
    // Create new chart
    anomalyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(rangeData),
            datasets: [{
                label: 'Number of Anomalies',
                data: Object.values(rangeData),
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Anomalies'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Anomaly Score Range'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Anomaly Score Distribution'
                }
            }
        }
    });
}

// Load activities data
function loadActivities() {
    return fetch(`${API_BASE_URL}/activities?hours=${timeRange}&limit=500`, {
        headers: { 'X-API-Key': API_KEY }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to load activities');
        return response.json();
    })
    .then(data => {
        console.log('Activities data:', data);
        activitiesData = data;
        
        // Update activities table
        updateActivitiesTable();
        
        return data;
    })
    .catch(error => {
        console.error('Error loading activities:', error);
        showAlert('error', 'Failed to load user activities. Please try again.');
        return [];
    });
}

// Update activities table with data
function updateActivitiesTable() {
    if (!activitiesTbody) return;
    
    // Filter activities based on selected user
    const filtered = filterActivitiesTable();
    
    if (filtered.length === 0) {
        activitiesTbody.innerHTML = '<tr><td colspan="7" class="text-center">No activities found for the selected filters</td></tr>';
        return;
    }
    
    // Clear existing table
    activitiesTbody.innerHTML = '';
    
    // Add rows for each activity
    filtered.forEach(activity => {
        const row = document.createElement('tr');
        
        // Format timestamp for display
        const timestamp = new Date(activity.timestamp);
        const formattedTime = timestamp.toLocaleString();
        
        // Determine anomaly class based on anomaly score
        let anomalyClass = 'normal';
        if (activity.anomaly_score >= 0.7) {
            anomalyClass = 'critical';
        } else if (activity.anomaly_score >= 0.5) {
            anomalyClass = 'high';
        } else if (activity.anomaly_score >= 0.3) {
            anomalyClass = 'medium';
        } else if (activity.anomaly_score >= 0.1) {
            anomalyClass = 'low';
        }
        
        // Extract success status from details
        const success = activity.details && activity.details.success;
        const successClass = success ? 'success-true' : 'success-false';
        const successText = success ? 'Success' : 'Failed';
        
        // Create table row
        row.innerHTML = `
            <td>${activity.username}</td>
            <td>${activity.activity_type.replace('_', ' ')}</td>
            <td class="resource-cell">${activity.resource}</td>
            <td>${activity.ip_address}</td>
            <td>${formattedTime}</td>
            <td class="${successClass}">${successText}</td>
            <td class="anomaly-${anomalyClass}">${activity.anomaly_score.toFixed(2)}</td>
            <td>
                <button class="btn btn-sm view-details-btn" onclick="viewActivityDetails(${activity.id})">View Details</button>
            </td>
        `;
        
        activitiesTbody.appendChild(row);
    });
}

// Filter activities based on user selection and search terms
function filterActivitiesTable() {
    const searchTerm = activitiesSearch ? activitiesSearch.value.toLowerCase() : '';
    
    return activitiesData.filter(activity => {
        // Filter by selected user
        if (selectedUser !== 'all' && activity.user_id.toString() !== selectedUser) {
            return false;
        }
        
        // Filter by search term
        if (searchTerm) {
            return (
                activity.username.toLowerCase().includes(searchTerm) ||
                activity.activity_type.toLowerCase().includes(searchTerm) ||
                activity.resource.toLowerCase().includes(searchTerm) ||
                activity.ip_address.toLowerCase().includes(searchTerm)
            );
        }
        
        return true;
    });
}

// View detailed information about an activity
function viewActivityDetails(activityId) {
    const activity = activitiesData.find(a => a.id === activityId);
    if (!activity) return;
    
    // Get the modal elements
    const modal = document.getElementById('activity-details-modal');
    const modalContent = document.getElementById('activity-details-content');
    
    if (!modal || !modalContent) return;
    
    // Format timestamp
    const timestamp = new Date(activity.timestamp);
    const formattedTime = timestamp.toLocaleString();
    
    // Create details HTML
    let detailsHtml = `
        <h3>Activity #${activity.id}</h3>
        <div class="details-grid">
            <div class="detail-item">
                <div class="detail-label">User</div>
                <div class="detail-value">${activity.username}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Activity Type</div>
                <div class="detail-value">${activity.activity_type.replace('_', ' ')}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Resource</div>
                <div class="detail-value">${activity.resource}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">IP Address</div>
                <div class="detail-value">${activity.ip_address}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Timestamp</div>
                <div class="detail-value">${formattedTime}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Anomaly Score</div>
                <div class="detail-value anomaly-${activity.anomaly_score >= 0.5 ? 'high' : 'low'}">${activity.anomaly_score.toFixed(2)}</div>
            </div>
        </div>
    `;
    
    // Add details from the details field if available
    if (activity.details) {
        detailsHtml += '<h4>Additional Details</h4><div class="details-grid">';
        
        for (const [key, value] of Object.entries(activity.details)) {
            detailsHtml += `
                <div class="detail-item">
                    <div class="detail-label">${key.replace('_', ' ')}</div>
                    <div class="detail-value">${value}</div>
                </div>
            `;
        }
        
        detailsHtml += '</div>';
    }
    
    // Set modal content
    modalContent.innerHTML = detailsHtml;
    
    // Show modal
    modal.style.display = 'block';
    
    // Close modal when clicking the X
    const closeButtons = modal.querySelectorAll('.close-modal, .modal-close-btn');
    closeButtons.forEach(button => {
        button.onclick = () => {
            modal.style.display = 'none';
        };
    });
    
    // Close modal when clicking outside of content
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
}

// Update activity timeline chart
function updateActivityTimeline() {
    const timelineCanvas = document.getElementById('timeline-chart');
    if (!timelineCanvas) return;
    
    // Filter activities based on selected user
    const activities = selectedUser === 'all' 
        ? activitiesData 
        : activitiesData.filter(activity => activity.user_id.toString() === selectedUser);
    
    if (activities.length === 0) {
        if (timelineChart) {
            timelineChart.destroy();
            timelineChart = null;
        }
        
        const ctx = timelineCanvas.getContext('2d');
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No activities found for the selected user', timelineCanvas.width / 2, timelineCanvas.height / 2);
        return;
    }
    
    // Group activities by day and type
    const activityByDay = {};
    const activityTypes = new Set();
    
    activities.forEach(activity => {
        // Get day from timestamp
        const date = new Date(activity.timestamp);
        const day = date.toISOString().split('T')[0];
        
        // Create entry for day if it doesn't exist
        if (!activityByDay[day]) {
            activityByDay[day] = {};
        }
        
        // Create entry for activity type if it doesn't exist
        if (!activityByDay[day][activity.activity_type]) {
            activityByDay[day][activity.activity_type] = 0;
        }
        
        // Increment count
        activityByDay[day][activity.activity_type]++;
        
        // Add activity type to set of all types
        activityTypes.add(activity.activity_type);
    });
    
    // Sort days
    const days = Object.keys(activityByDay).sort();
    
    // Convert activity types set to array and sort
    const typesList = Array.from(activityTypes).sort();
    
    // Prepare datasets for each activity type
    const datasets = typesList.map((type, index) => {
        // Generate a color based on index
        const hue = Math.floor(360 * (index / typesList.length));
        const color = `hsla(${hue}, 70%, 60%, 0.8)`;
        
        // Create data array
        const data = days.map(day => activityByDay[day][type] || 0);
        
        return {
            label: type.replace('_', ' '),
            data: data,
            backgroundColor: color,
            borderColor: color,
            borderWidth: 1
        };
    });
    
    // If a chart already exists, destroy it
    if (timelineChart) {
        timelineChart.destroy();
    }
    
    // Create new chart
    const ctx = timelineCanvas.getContext('2d');
    timelineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days.map(day => {
                const date = new Date(day);
                return date.toLocaleDateString();
            }),
            datasets: datasets
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Activity Count'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: selectedUser === 'all' ? 'Activity Timeline - All Users' : `Activity Timeline - User ${getUsernameById(selectedUser)}`
                }
            }
        }
    });
}

// Get username by user ID
function getUsernameById(userId) {
    const user = usersList.find(u => u.user_id.toString() === userId);
    return user ? user.username : `User ${userId}`;
}

// Update the feature chart showing anomaly factors
function updateFeatureChart() {
    const featureCanvas = document.getElementById('feature-chart');
    if (!featureCanvas) return;
    
    // Get features based on the selected user
    const features = generateFeatureData();
    
    // If no features are available, display a message
    if (features.length === 0) {
        if (featureChart) {
            featureChart.destroy();
            featureChart = null;
        }
        
        const ctx = featureCanvas.getContext('2d');
        ctx.clearRect(0, 0, featureCanvas.width, featureCanvas.height);
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No feature data available', featureCanvas.width / 2, featureCanvas.height / 2);
        return;
    }
    
    // Extract feature names and values
    const featureNames = features.map(f => formatFeatureName(f.name));
    const featureValues = features.map(f => f.value);
    const featureColors = features.map(f => getColorForValue(f.value));
    
    // If a chart already exists, destroy it
    if (featureChart) {
        featureChart.destroy();
    }
    
    // Create new chart
    const ctx = featureCanvas.getContext('2d');
    featureChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: featureNames,
            datasets: [{
                label: 'Feature Values',
                data: featureValues,
                backgroundColor: featureColors.map(color => color.replace('1)', '0.2)')),
                borderColor: featureColors,
                borderWidth: 2,
                pointBackgroundColor: featureColors,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: featureColors
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        stepSize: 0.2
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Anomaly Feature Analysis'
                }
            }
        }
    });
}

// Generate feature data for the selected user
function generateFeatureData() {
    // If no user is selected, return empty array
    if (!selectedUser || selectedUser === 'all') {
        return [];
    }
    
    // Generate synthetic feature data for demonstration
    return [
        { name: 'login_time', value: Math.random() * 0.8 + 0.2 },
        { name: 'access_frequency', value: Math.random() * 0.8 + 0.2 },
        { name: 'resource_access', value: Math.random() * 0.8 + 0.2 },
        { name: 'ip_location', value: Math.random() * 0.8 + 0.2 },
        { name: 'session_duration', value: Math.random() * 0.8 + 0.2 },
        { name: 'device_type', value: Math.random() * 0.8 + 0.2 }
    ];
}

// Format feature name for display
function formatFeatureName(name) {
    return name.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Get color based on feature value
function getColorForValue(value) {
    if (value >= 0.8) return 'rgba(255, 99, 132, 1)';  // Red
    if (value >= 0.6) return 'rgba(255, 159, 64, 1)';  // Orange
    if (value >= 0.4) return 'rgba(255, 205, 86, 1)';  // Yellow
    if (value >= 0.2) return 'rgba(75, 192, 192, 1)';  // Green
    return 'rgba(54, 162, 235, 1)';  // Blue
}

// Export activities to CSV
function exportActivities() {
    // Filter activities based on selected user and search term
    const searchTerm = activitiesSearch.value.toLowerCase();
    const filteredActivities = activitiesData.filter(activity => {
        // Filter by user if a specific user is selected
        if (selectedUser !== 'all' && activity.user_id.toString() !== selectedUser) {
            return false;
        }
        
        // Filter by search term
        if (searchTerm) {
            return (
                activity.username.toLowerCase().includes(searchTerm) ||
                activity.activity_type.toLowerCase().includes(searchTerm) ||
                (activity.resource && activity.resource.toLowerCase().includes(searchTerm)) ||
                activity.ip_address.toLowerCase().includes(searchTerm)
            );
        }
        
        return true;
    });
    
    if (filteredActivities.length === 0) {
        showAlert('error', 'No activities to export');
        return;
    }
    
    // Create CSV content
    const headers = [
        'ID', 'User', 'Activity Type', 'Resource', 'IP Address', 
        'Timestamp', 'Anomaly Score'
    ];
    
    let csvContent = headers.join(',') + '\n';
    
    filteredActivities.forEach(activity => {
        const row = [
            activity.id,
            `"${activity.username}"`,
            `"${activity.activity_type}"`,
            `"${activity.resource || 'N/A'}"`,
            activity.ip_address,
            activity.timestamp,
            activity.anomaly_score.toFixed(3)
        ];
        
        csvContent += row.join(',') + '\n';
    });
    
    // Create and download the CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    link.setAttribute('href', url);
    link.setAttribute('download', `ueba_activities_${formatDateForFilename(new Date())}.csv`);
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Helper functions

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

// Format date and time
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Format date for filename
function formatDateForFilename(date) {
    return date.toISOString().split('T')[0];
}

// Get risk level from score
function getRiskLevel(score) {
    if (score >= 0.8) return 'critical';
    if (score >= 0.6) return 'high';
    if (score >= 0.4) return 'medium';
    if (score >= 0.2) return 'low';
    return 'normal';
}

// Get CSS class for risk level
function getRiskLevelClass(score) {
    return `risk-level-${getRiskLevel(score)}`;
}

// Format factor name for display
function formatFactorName(factor) {
    return factor
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
}

// Make viewActivityDetails available globally
window.viewActivityDetails = viewActivityDetails;
window.viewUserActivities = viewUserActivities; 