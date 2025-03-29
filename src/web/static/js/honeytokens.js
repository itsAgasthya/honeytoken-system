// Honeytoken Management JS
// API communication and UI handling for the honeytokens page

// Configuration
const API_KEY = "honeytoken_api_key_123";
const API_BASE_URL = "/api";

// DOM Elements
let honeytokensList;
let createHoneytokenBtn;
let createHoneytokenModal;
let honeytokenForm;
let closeModalBtn;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    honeytokensList = document.getElementById('honeytokens-list');
    createHoneytokenBtn = document.getElementById('create-honeytoken-btn');
    createHoneytokenModal = document.getElementById('create-honeytoken-modal');
    honeytokenForm = document.getElementById('honeytoken-form');
    closeModalBtn = document.querySelector('.close-modal');
    
    // Add event listeners
    if (createHoneytokenBtn) {
        createHoneytokenBtn.addEventListener('click', showCreateModal);
    }
    
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', hideModal);
    }
    
    if (honeytokenForm) {
        honeytokenForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Load honeytokens on page load
    loadHoneytokens();
    
    // Handle type selection changes
    const tokenTypeSelect = document.getElementById('token-type');
    if (tokenTypeSelect) {
        tokenTypeSelect.addEventListener('change', function() {
            updateFormFields(this.value);
        });
    }
});

// Load and display honeytokens
function loadHoneytokens() {
    fetch(`${API_BASE_URL}/honeytokens`, {
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
        displayHoneytokens(data);
    })
    .catch(error => {
        console.error('Error loading honeytokens:', error);
        showErrorMessage('Failed to load honeytokens. Please try again later.');
    });
}

// Display honeytokens in the UI
function displayHoneytokens(honeytokens) {
    if (!honeytokensList) return;
    
    // Clear existing content
    honeytokensList.innerHTML = '';
    
    if (honeytokens.length === 0) {
        honeytokensList.innerHTML = '<div class="empty-state">No honeytokens found. Create your first honeytoken to get started!</div>';
        return;
    }
    
    // Create a card for each honeytoken
    honeytokens.forEach(token => {
        const card = document.createElement('div');
        card.className = 'honeytoken-card';
        card.dataset.id = token.id;
        
        // Set card color based on token type
        const typeClass = getTypeClass(token.type);
        card.classList.add(typeClass);
        
        // Format the created date
        const createdDate = new Date(token.created_at).toLocaleDateString();
        
        card.innerHTML = `
            <div class="card-header">
                <h3>${token.name || 'Unnamed Token'}</h3>
                <span class="token-type">${token.type}</span>
            </div>
            <div class="card-body">
                <p>${token.description || 'No description'}</p>
                <div class="token-details">
                    <span>Created: ${createdDate}</span>
                    <span>Location: ${token.location || 'N/A'}</span>
                </div>
            </div>
            <div class="card-actions">
                <button class="btn btn-sm btn-view" data-id="${token.id}">View</button>
                <button class="btn btn-sm btn-edit" data-id="${token.id}">Edit</button>
                <button class="btn btn-sm btn-delete" data-id="${token.id}">Delete</button>
            </div>
        `;
        
        honeytokensList.appendChild(card);
        
        // Add event listeners for the buttons
        card.querySelector('.btn-view').addEventListener('click', () => viewHoneytoken(token.id));
        card.querySelector('.btn-edit').addEventListener('click', () => editHoneytoken(token.id));
        card.querySelector('.btn-delete').addEventListener('click', () => deleteHoneytoken(token.id));
    });
}

// Get a CSS class based on token type
function getTypeClass(type) {
    switch(type) {
        case 'file': return 'token-file';
        case 'database': return 'token-database';
        case 'api_key': return 'token-api';
        case 'credentials': return 'token-credentials';
        default: return 'token-default';
    }
}

// Show the create honeytoken modal
function showCreateModal() {
    if (createHoneytokenModal) {
        createHoneytokenModal.classList.add('show');
        // Reset form
        if (honeytokenForm) {
            honeytokenForm.reset();
            document.getElementById('token-id').value = '';
            updateFormFields(document.getElementById('token-type').value);
        }
    }
}

// Hide the modal
function hideModal() {
    if (createHoneytokenModal) {
        createHoneytokenModal.classList.remove('show');
    }
}

// Update form fields based on token type
function updateFormFields(tokenType) {
    // Hide all type-specific fields
    document.querySelectorAll('.type-specific').forEach(el => {
        el.style.display = 'none';
    });
    
    // Show fields specific to the selected type
    const fieldsToShow = document.querySelectorAll(`.${tokenType}-fields`);
    fieldsToShow.forEach(el => {
        el.style.display = 'block';
    });
}

// Handle form submission
function handleFormSubmit(e) {
    e.preventDefault();
    
    const tokenId = document.getElementById('token-id').value;
    const isEdit = tokenId !== '';
    
    // Get form data
    const formData = {
        name: document.getElementById('token-name').value,
        token_type: document.getElementById('token-type').value,
        description: document.getElementById('token-description').value,
        sensitivity: document.getElementById('token-sensitivity').value
    };
    
    // Add type-specific data
    switch(formData.token_type) {
        case 'file':
            formData.file_path = document.getElementById('file-path').value;
            formData.content = document.getElementById('file-content').value;
            break;
        case 'database':
            formData.table_name = document.getElementById('table-name').value;
            formData.record_data = document.getElementById('record-data').value;
            break;
        case 'api_key':
            formData.service_name = document.getElementById('service-name').value;
            formData.key_prefix = document.getElementById('key-prefix').value;
            break;
        case 'credentials':
            formData.username = document.getElementById('username').value;
            formData.service = document.getElementById('service').value;
            break;
    }
    
    // API endpoint and method
    let url = `${API_BASE_URL}/honeytokens`;
    let method = 'POST';
    
    if (isEdit) {
        url = `${url}/${tokenId}`;
        method = 'PUT';
    }
    
    // Make API request
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Success
        hideModal();
        showSuccessMessage(isEdit ? 'Honeytoken updated successfully' : 'Honeytoken created successfully');
        loadHoneytokens(); // Reload the list
    })
    .catch(error => {
        console.error('Error saving honeytoken:', error);
        showErrorMessage('Failed to save honeytoken. Please try again.');
    });
}

// View honeytoken details
function viewHoneytoken(id) {
    fetch(`${API_BASE_URL}/honeytokens/${id}`, {
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
    .then(token => {
        // Display token details in a modal or panel
        showTokenDetails(token);
    })
    .catch(error => {
        console.error('Error fetching honeytoken details:', error);
        showErrorMessage('Failed to retrieve honeytoken details.');
    });
}

// Show token details in a modal
function showTokenDetails(token) {
    // Implementation depends on your UI design
    alert(`Honeytoken: ${token.name}\nType: ${token.token_type}\nValue: ${token.value}`);
}

// Edit a honeytoken
function editHoneytoken(id) {
    fetch(`${API_BASE_URL}/honeytokens/${id}`, {
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
    .then(token => {
        // Populate the form with token data
        document.getElementById('token-id').value = token.token_id;
        document.getElementById('token-name').value = token.name || '';
        document.getElementById('token-type').value = token.token_type;
        document.getElementById('token-description').value = token.description || '';
        document.getElementById('token-sensitivity').value = token.sensitivity || 'medium';
        
        // Populate type-specific fields
        updateFormFields(token.token_type);
        
        // Show the modal
        showCreateModal();
    })
    .catch(error => {
        console.error('Error fetching honeytoken for edit:', error);
        showErrorMessage('Failed to retrieve honeytoken data for editing.');
    });
}

// Delete a honeytoken
function deleteHoneytoken(id) {
    if (!confirm('Are you sure you want to delete this honeytoken? This action cannot be undone.')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/honeytokens/${id}`, {
        method: 'DELETE',
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
        showSuccessMessage('Honeytoken deleted successfully');
        loadHoneytokens(); // Reload the list
    })
    .catch(error => {
        console.error('Error deleting honeytoken:', error);
        showErrorMessage('Failed to delete honeytoken. Please try again.');
    });
}

// Show a success message
function showSuccessMessage(message) {
    // Implementation depends on your UI design
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success';
        alert.textContent = message;
        alertContainer.appendChild(alert);
        
        // Remove after 3 seconds
        setTimeout(() => {
            alert.remove();
        }, 3000);
    } else {
        alert(message);
    }
}

// Show an error message
function showErrorMessage(message) {
    // Implementation depends on your UI design
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.textContent = message;
        alertContainer.appendChild(alert);
        
        // Remove after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    } else {
        alert(message);
    }
} 