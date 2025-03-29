// User Management JS
// API communication and UI handling for the users page

// Configuration
const API_KEY = 'honeytoken_api_key_123'; // Hardcoded API key for demo purposes
const API_BASE_URL = '/api';

// DOM Elements
let usersTbody;
let userSearch;
let userFilter;
let refreshBtn;
let modal;

// Data storage
let usersData = [];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    usersTbody = document.getElementById('users-tbody');
    userSearch = document.getElementById('user-search');
    userFilter = document.getElementById('user-filter');
    refreshBtn = document.getElementById('refresh-users-btn');
    modal = document.getElementById('user-details-modal');
    
    // Set up event listeners
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadData);
    }
    
    if (userSearch) {
        userSearch.addEventListener('input', filterUsers);
    }
    
    if (userFilter) {
        userFilter.addEventListener('change', filterUsers);
    }
    
    // Close modal when clicking on the X or outside
    const closeModalElements = document.querySelectorAll('.close-modal, .modal-close-btn');
    closeModalElements.forEach(element => {
        element.addEventListener('click', closeModal);
    });
    
    // Click outside to close
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });
    
    // View in UEBA button
    const viewUebaBtn = document.getElementById('view-ueba-btn');
    if (viewUebaBtn) {
        viewUebaBtn.addEventListener('click', function() {
            const userId = modal.dataset.userId;
            if (userId) {
                window.location.href = `/ueba?user=${userId}`;
            }
        });
    }
    
    // Load initial data
    loadData();
});

// Load all users data
function loadData() {
    // Show loading state
    if (usersTbody) {
        usersTbody.innerHTML = '<tr class="loading-row"><td colspan="7">Loading users...</td></tr>';
    }
    
    // Update overview stats
    updateUserStats();
    
    // Load users
    fetch(`${API_BASE_URL}/users`, {
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
        usersData = data;
        displayUsers(data);
    })
    .catch(error => {
        console.error('Error loading users:', error);
        if (usersTbody) {
            usersTbody.innerHTML = '<tr class="error-row"><td colspan="7">Failed to load users. Please try again.</td></tr>';
        }
        showAlert('error', 'Failed to load users. Please try again later.');
    });
}

// Display users in the table
function displayUsers(users) {
    if (!usersTbody) return;
    
    if (!users || users.length === 0) {
        usersTbody.innerHTML = '<tr><td colspan="7" class="text-center">No users found</td></tr>';
        return;
    }
    
    usersTbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.className = 'user-row';
        row.setAttribute('data-user-id', user.id);
        
        // Format timestamps
        const lastLoginDate = user.last_login ? new Date(user.last_login) : null;
        const lastActivityDate = user.last_activity ? new Date(user.last_activity) : null;
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.role}</td>
            <td>${lastLoginDate ? lastLoginDate.toLocaleDateString() : 'Never'}</td>
            <td>${lastActivityDate ? lastActivityDate.toLocaleDateString() : 'Never'}</td>
            <td>
                <button class="btn btn-sm btn-primary view-user" data-id="${user.id}">View</button>
                <button class="btn btn-sm btn-danger delete-user" data-id="${user.id}">Delete</button>
            </td>
        `;
        
        usersTbody.appendChild(row);
    });
    
    // Add event listeners to buttons
    usersTbody.querySelectorAll('.view-user').forEach(btn => {
        btn.addEventListener('click', () => viewUser(btn.dataset.id));
    });
    
    usersTbody.querySelectorAll('.delete-user').forEach(btn => {
        btn.addEventListener('click', () => deleteUser(btn.dataset.id));
    });
}

// Filter users based on search and filter selection
function filterUsers() {
    if (!usersData.length) return;
    
    const searchTerm = userSearch.value.toLowerCase();
    const filterValue = userFilter.value;
    
    const filteredUsers = usersData.filter(user => {
        // Filter by search term
        const matchesSearch = 
            user.username.toLowerCase().includes(searchTerm) ||
            (user.department && user.department.toLowerCase().includes(searchTerm)) ||
            (user.role && user.role.toLowerCase().includes(searchTerm));
        
        // Filter by user type
        let matchesFilter = true;
        if (filterValue === 'admin') {
            matchesFilter = user.role === 'admin';
        } else if (filterValue === 'regular') {
            matchesFilter = user.role !== 'admin';
        }
        
        return matchesSearch && matchesFilter;
    });
    
    displayUsers(filteredUsers);
}

// Update user statistics in the overview section
function updateUserStats() {
    fetch(`${API_BASE_URL}/users/stats`, {
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
        document.getElementById('total-users').textContent = data.total || 0;
        document.getElementById('active-users').textContent = data.active || 0;
        document.getElementById('admin-users').textContent = data.admin || 0;
        document.getElementById('risky-users').textContent = data.risky || 0;
    })
    .catch(error => {
        console.error('Error loading user stats:', error);
    });
}

// View user details
function viewUser(userId) {
    fetch(`${API_BASE_URL}/users/${userId}`, {
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
    .then(user => {
        showUserDetails(user);
        loadUserRisk(userId);
        loadUserActivities(userId);
    })
    .catch(error => {
        console.error('Error loading user details:', error);
        showAlert('error', 'Failed to load user details.');
    });
}

// View user activity history
function viewUserHistory(userId) {
    window.location.href = `/ueba?user=${userId}`;
}

// Show user details in modal
function showUserDetails(user) {
    const modal = document.getElementById('userDetailsModal');
    if (!modal) return;
    
    const modalContent = modal.querySelector('.modal-body');
    modalContent.innerHTML = `
        <div class="user-details">
            <h5>User Details</h5>
            <p><strong>ID:</strong> ${user.id}</p>
            <p><strong>Username:</strong> ${user.username}</p>
            <p><strong>Email:</strong> ${user.email}</p>
            <p><strong>Role:</strong> ${user.role}</p>
            <p><strong>Department:</strong> ${user.department || 'N/A'}</p>
            <p><strong>Created:</strong> ${new Date(user.created_at).toLocaleString()}</p>
            <p><strong>Last Login:</strong> ${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</p>
            <p><strong>Last Activity:</strong> ${user.last_activity ? new Date(user.last_activity).toLocaleString() : 'Never'}</p>
            <p><strong>Status:</strong> ${user.status}</p>
        </div>
    `;
    
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

// Load user risk information
function loadUserRisk(userId) {
    fetch(`${API_BASE_URL}/users/${userId}/risk`, {
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
        updateRiskMeter(data.risk_score);
        updateRiskFactors(data.risk_factors);
    })
    .catch(error => {
        console.error('Error loading user risk:', error);
        document.getElementById('risk-meter-fill').style.width = '0%';
        document.getElementById('risk-score-label').textContent = 'Risk Score: N/A';
        document.getElementById('risk-factors-list').innerHTML = '<li>Failed to load risk factors</li>';
    });
}

// Update the risk meter display
function updateRiskMeter(riskScore) {
    const riskMeterFill = document.getElementById('risk-meter-fill');
    const riskScoreLabel = document.getElementById('risk-score-label');
    
    if (riskMeterFill && riskScoreLabel) {
        const percentage = Math.min(Math.max(riskScore * 100, 0), 100);
        riskMeterFill.style.width = `${percentage}%`;
        riskMeterFill.className = `progress-bar ${getRiskClass(riskScore)}`;
        riskScoreLabel.textContent = `Risk Score: ${(riskScore * 100).toFixed(1)}%`;
    }
}

// Update risk factors list
function updateRiskFactors(factors) {
    const riskFactorsList = document.getElementById('risk-factors-list');
    if (!riskFactorsList) return;
    
    if (!factors || factors.length === 0) {
        riskFactorsList.innerHTML = '<li>No risk factors identified</li>';
        return;
    }
    
    riskFactorsList.innerHTML = factors.map(factor => `
        <li class="${getRiskClass(factor.risk_score)}">
            ${factor.description} (Risk: ${(factor.risk_score * 100).toFixed(1)}%)
        </li>
    `).join('');
}

// Load user activities
function loadUserActivities(userId) {
    fetch(`${API_BASE_URL}/users/${userId}/activities`, {
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
        updateUserActivities(data);
    })
    .catch(error => {
        console.error('Error loading user activities:', error);
        document.getElementById('user-activities').innerHTML = '<div class="alert alert-danger">Failed to load user activities</div>';
    });
}

// Update user activities
function updateUserActivities(activities) {
    const activitiesContainer = document.getElementById('user-activities');
    if (!activitiesContainer) return;
    
    if (!activities || activities.length === 0) {
        activitiesContainer.innerHTML = '<div class="alert alert-info">No activities found for this user</div>';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Activity Type</th>
                <th>Details</th>
                <th>Risk Score</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;
    
    const tbody = table.querySelector('tbody');
    
    activities.forEach(activity => {
        const row = document.createElement('tr');
        row.className = `activity-row ${getRiskClass(activity.risk_score)}`;
        
        row.innerHTML = `
            <td>${new Date(activity.timestamp).toLocaleString()}</td>
            <td>${activity.type}</td>
            <td>${activity.details}</td>
            <td>${(activity.risk_score * 100).toFixed(1)}%</td>
        `;
        
        tbody.appendChild(row);
    });
    
    activitiesContainer.innerHTML = '';
    activitiesContainer.appendChild(table);
}

// Close the modal
function closeModal() {
    if (modal) {
        modal.style.display = 'none';
    }
}

// Helper Functions

// Format date to human-readable string
function formatDate(date) {
    return date.toLocaleString();
}

// Get CSS class for risk level
function getRiskClass(score) {
    if (score >= 0.8) return 'high-risk';
    if (score >= 0.6) return 'medium-risk';
    if (score >= 0.4) return 'low-risk';
    return 'no-risk';
}

// Get user initials for avatar placeholder
function getInitials(name) {
    if (!name) return '?';
    
    return name
        .split(' ')
        .map(part => part.charAt(0).toUpperCase())
        .join('')
        .substring(0, 2);
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