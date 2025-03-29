// Alerts Management JS
// API communication and UI handling for the alerts page

// Configuration
const API_KEY = "honeytoken_api_key_123";
const API_BASE_URL = "/api";

// DOM elements
let alertsList;
let filterControls;
let alertSummary;

// Initialization
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    alertsList = document.getElementById('alerts-list');
    filterControls = document.getElementById('filter-controls');
    alertSummary = document.getElementById('alert-summary');
    
    // Set up event listeners
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadAlerts();
        });
    }
    
    // Load initial data
    loadAlertSummary();
    loadAlerts();
});

// Load alert summary statistics
function loadAlertSummary() {
    fetch(`${API_BASE_URL}/alerts/summary`, {
        headers: {
            'X-API-Key': API_KEY
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        updateAlertSummary(data);
    })
    .catch(error => {
        console.error('Error loading alert summary:', error);
        showErrorMessage('Failed to load alert summary. Please try again later.');
    });
}

// Update alert summary in the UI
function updateAlertSummary(summary) {
    if (!alertSummary) return;
    
    // Update count elements
    document.getElementById('critical-count').textContent = summary.critical || 0;
    document.getElementById('high-count').textContent = summary.high || 0;
    document.getElementById('medium-count').textContent = summary.medium || 0;
    document.getElementById('low-count').textContent = summary.low || 0;
    
    // Calculate total
    const total = (summary.critical || 0) + (summary.high || 0) + (summary.medium || 0) + (summary.low || 0);
    document.getElementById('total-count').textContent = total;
}

// Load alerts with optional filters
function loadAlerts() {
    // Get filter values if the filter form exists
    let filterParams = '';
    const filterForm = document.getElementById('filter-form');
    
    if (filterForm) {
        const severity = document.getElementById('filter-severity').value;
        const resolved = document.getElementById('filter-resolved').value;
        const hours = document.getElementById('filter-hours').value || 24;
        
        filterParams = new URLSearchParams();
        if (severity && severity !== 'all') {
            filterParams.append('severity', severity);
        }
        if (resolved && resolved !== 'all') {
            filterParams.append('resolved', resolved === 'true');
        }
        filterParams.append('hours', hours);
    } else {
        // Default to recent alerts
        filterParams = new URLSearchParams({
            hours: 24
        });
    }
    
    // Show loading state
    const alertsList = document.getElementById('alerts-list');
    if (alertsList) {
        alertsList.innerHTML = '<div class="text-center p-4">Loading alerts...</div>';
    }
    
    // Make API request
    fetch(`${API_BASE_URL}/alerts/recent?${filterParams}`, {
        headers: {
            'X-API-Key': API_KEY
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        displayAlerts(data);
    })
    .catch(error => {
        console.error('Error loading alerts:', error);
        if (alertsList) {
            alertsList.innerHTML = '<div class="alert alert-danger">Failed to load alerts. Please try again later.</div>';
        }
        showErrorMessage('Failed to load alerts. Please try again later.');
    });
}

// Display alerts in the table
function displayAlerts(alerts) {
    const alertsList = document.getElementById('alerts-list');
    if (!alertsList) return;
    
    if (!alerts || alerts.length === 0) {
        alertsList.innerHTML = '<div class="text-center p-4">No alerts found</div>';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover';
    table.innerHTML = `
        <thead>
            <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Severity</th>
                <th>User</th>
                <th>Timestamp</th>
                <th>Description</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;
    
    const tbody = table.querySelector('tbody');
    
    alerts.forEach(alert => {
        const statusClass = alert.status ? 'badge-success' : 'badge-warning';
        const statusText = alert.status ? 'Resolved' : 'Open';
        
        const row = document.createElement('tr');
        row.className = 'alert-row';
        row.setAttribute('data-alert-id', alert.id);
        
        // Format timestamp for display
        const timestamp = new Date(alert.timestamp);
        const formattedDate = timestamp.toLocaleDateString();
        const formattedTime = timestamp.toLocaleTimeString();
        
        row.innerHTML = `
            <td>${alert.id}</td>
            <td>${alert.alert_type || 'Unknown'}</td>
            <td><span class="severity-${alert.severity}">${alert.severity}</span></td>
            <td>${alert.username || 'Unknown'}</td>
            <td>${formattedDate}<br><small>${formattedTime}</small></td>
            <td>${alert.description}</td>
            <td><span class="badge ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-sm btn-primary view-alert" data-id="${alert.id}">View</button>
                ${!alert.status ? `<button class="btn btn-sm btn-success resolve-alert" data-id="${alert.id}">Resolve</button>` : ''}
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Clear and update the alerts list
    alertsList.innerHTML = '';
    alertsList.appendChild(table);
    
    // Add event listeners to buttons
    alertsList.querySelectorAll('.view-alert').forEach(btn => {
        btn.addEventListener('click', () => viewAlert(btn.dataset.id));
    });
    
    alertsList.querySelectorAll('.resolve-alert').forEach(btn => {
        btn.addEventListener('click', () => resolveAlert(btn.dataset.id));
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
        showErrorMessage('Failed to load alert details.');
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
        showSuccessMessage('Alert resolved successfully');
        loadAlerts(); // Refresh alerts list
    })
    .catch(error => {
        console.error('Error resolving alert:', error);
        showErrorMessage('Failed to resolve alert.');
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
            <p><strong>Type:</strong> ${alert.alert_type || 'Unknown'}</p>
            <p><strong>Severity:</strong> ${alert.severity}</p>
            <p><strong>User:</strong> ${alert.username || 'Unknown'}</p>
            <p><strong>Timestamp:</strong> ${new Date(alert.timestamp).toLocaleString()}</p>
            <p><strong>Description:</strong> ${alert.description}</p>
            <p><strong>Source:</strong> ${alert.source || 'Unknown'}</p>
            <p><strong>Status:</strong> ${alert.status ? 'Resolved' : 'Open'}</p>
            ${alert.resolution_notes ? `<p><strong>Resolution Notes:</strong> ${alert.resolution_notes}</p>` : ''}
        </div>
    `;
    
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

// Show error message
function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
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

// Show success message
function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
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